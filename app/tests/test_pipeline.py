import asyncio
from dataclasses import asdict
from io import BytesIO
import json
from pathlib import Path
import sys
import tempfile
from threading import Event
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
import soundfile as sf
import torch
from torch import nn
import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.preprocessing.audio_processor import AudioProcessor, AudioValidationError
from src.acoustic.parselmouth_extractor import ParselmouthExtractor
from src.acoustic.physical_rules import PhysicalRulesEngine
from src.ai_models.model_utils import probabilities, classification, cosine_classification, exact_state, windows
from src.ai_models.age_gender_model import AgeGenderPredictor
from src.ai_models.emotion_accent_model import EmotionAccentPredictor
from src.core.data_models import AcousticFeatures, DemographicProfile, EmotionalState, Prediction, AudioQuality
from src.core.hybrid_engine import HybridEngine


def wav(samples, sr=16000):
    buffer = BytesIO()
    sf.write(buffer, samples, sr, format='WAV', subtype='FLOAT')
    return buffer.getvalue()


class SignalTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / 'audio.wav'
        self.sr = 16000
        t = np.arange(self.sr * 3) / self.sr
        self.tone = (0.03 * np.sin(2 * np.pi * 200 * t)).astype('float32')

    def tearDown(self):
        self.directory.cleanup()

    def write(self, values, sr=16000):
        sf.write(self.path, values, sr, subtype='FLOAT')

    def test_preserves_gain_and_does_not_turn_whisper_into_full_scale(self):
        self.write(self.tone)
        audio, quality = AudioProcessor().process_with_quality(self.path)
        self.assertAlmostEqual(float(np.max(np.abs(audio))), 0.03, places=4)
        self.assertAlmostEqual(quality.rms_dbfs, 20 * np.log10(0.03 / np.sqrt(2)), places=2)

    def test_silence_short_and_corrupt_are_rejected(self):
        for values in [np.zeros(self.sr * 2), self.tone[:4000]]:
            self.write(values)
            with self.assertRaises(AudioValidationError):
                AudioProcessor().process(self.path)
        self.path.write_bytes(b'not audio')
        with self.assertRaises(AudioValidationError):
            AudioProcessor().process(self.path)

    def test_nonfinite_audio_is_rejected(self):
        self.write(np.full(self.sr * 2, np.nan))
        with self.assertRaises(AudioValidationError):
            AudioProcessor().process(self.path)

    def test_resamples_stereo_and_records_clipping_before_processing(self):
        t = np.arange(48000 * 2) / 48000
        loud = np.clip(2 * np.sin(2 * np.pi * 200 * t), -1, 1)
        self.write(np.column_stack([loud, loud]), 48000)
        audio, quality = AudioProcessor().process_with_quality(self.path)
        self.assertEqual(len(audio), 32000)
        self.assertGreater(quality.clipping_fraction, 0.1)
        self.assertTrue(any('saturación' in warning for warning in quality.warnings))

    def test_praat_pitch_and_unvoiced_missing_values(self):
        self.write(self.tone)
        measured = ParselmouthExtractor().extract_features(self.path)
        self.assertAlmostEqual(measured['f0_mean'], 200, delta=2)
        self.assertGreater(measured['voiced_fraction'], 0.9)
        self.write(np.zeros(self.sr * 2))
        measured = ParselmouthExtractor().extract_features(self.path)
        self.assertIsNone(measured['f0_mean'])
        self.assertIsNone(measured['jitter'])
        self.assertIsNone(measured['shimmer'])


class InferenceTests(unittest.TestCase):
    def test_log_probabilities_are_not_negative_percentages(self):
        np.testing.assert_allclose(probabilities(np.log([0.1, 0.8, 0.1])), [0.1, 0.8, 0.1])

    def test_language_similarities_are_preserved_and_not_softmaxed(self):
        result = cosine_classification([0.69, 0.16, -0.2], ['Spanish', 'Italian', 'French'], 'language')
        self.assertEqual(result.value, 'Spanish')
        self.assertEqual(result.score, 0.69)
        self.assertEqual(result.distribution['French'], -0.2)
        self.assertEqual(result.details['score_type'], 'cosine_similarity')
        ambiguous = cosine_classification([0.47, 0.44, 0.14], ['Italian', 'Esperanto', 'French'], 'language')
        self.assertIsNone(ambiguous.value)

    def test_ambiguous_result_abstains_and_retains_candidates(self):
        result = classification([0.34, 0.33, 0.33], ['a', 'b', 'c'], 'model')
        self.assertEqual(result.status, 'uncertain')
        self.assertIsNone(result.value)
        self.assertEqual(len(result.distribution), 3)

    def test_missing_trained_parameters_are_a_failure(self):
        with self.assertRaises(RuntimeError):
            exact_state(nn.Linear(2, 3), {'weight': torch.zeros(3, 2)})

    def test_age_uses_regression_output_and_all_three_vocal_classes(self):
        predictor = AgeGenderPredictor()
        predictor.state = 'ready'
        predictor.labels = ['female', 'male', 'child']
        predictor.processor = lambda audio, **kwargs: SimpleNamespace(input_values=torch.zeros(1, len(audio)))
        ages = []
        for fraction in [0.21, 0.58]:
            predictor.model = lambda values: (torch.tensor([[fraction]]), torch.tensor([[0.05, 0.05, 0.9]]))
            gender, age = predictor.predict(np.ones(16000 * 4, dtype='float32'))
            ages.append(age.value)
            self.assertEqual(gender.value, 'Voz infantil')
        self.assertEqual(ages, [21.0, 58.0])

    def test_model_failure_and_short_audio_do_not_fabricate_age(self):
        predictor = AgeGenderPredictor()
        _, short = predictor.predict(np.zeros(16000, dtype='float32'))
        self.assertEqual(short.status, 'insufficient_audio')
        predictor.state, predictor.error = 'unavailable', 'missing weights'
        gender, age = predictor.predict(np.zeros(16000 * 4, dtype='float32'))
        self.assertIsNone(age.value)
        self.assertIsNone(gender.value)
        self.assertEqual(age.status, 'unavailable')

    def test_language_and_accent_are_separate_models(self):
        predictor = EmotionAccentPredictor()
        predictor.lang_model.infer = lambda *args: Prediction(value='Spanish', status='ok', score=0.9)
        predictor.emotion_model.infer = lambda *args: Prediction(value='ang', status='ok', score=0.9, distribution={'ang': 0.9, 'neu': 0.1})
        with patch.object(predictor.accent_model, 'infer', return_value=Prediction(value='RIOPLATENSE', status='ok')) as accent:
            emotion, language, regional = predictor.predict(np.ones(16000 * 5, dtype='float32'))
            self.assertEqual(language.value, 'Spanish')
            self.assertEqual(regional.value, 'RIOPLATENSE')
            self.assertEqual(emotion.value, 'Enojo')
            self.assertTrue(emotion.details['outside_training_language'])
            accent.assert_called_once()
        predictor.lang_model.infer = lambda *args: Prediction(value='French', status='ok')
        with patch.object(predictor.accent_model, 'infer') as accent:
            _, _, regional = predictor.predict(np.ones(16000 * 5, dtype='float32'))
            self.assertEqual(regional.status, 'not_applicable')
            accent.assert_not_called()

    def test_long_inference_is_bounded_without_large_attention_inputs(self):
        chunks = windows(np.ones(16000 * 120, dtype='float32'))
        self.assertEqual(len(chunks), 3)
        self.assertTrue(all(len(chunk) <= 16000 * 6 for chunk in chunks))

    def test_acoustics_do_not_imply_smoking_stress_or_100_percent_reliability(self):
        acoustic = AcousticFeatures(jitter=0.09, shimmer=0.3, hnr=2, energy_rms=0.8, f0_std=40)
        physical = PhysicalRulesEngine().evaluate(acoustic)
        self.assertIsNone(physical.smoker_prob)
        self.assertIsNone(physical.fatigue_prob)
        self.assertIsNone(physical.respiratory_anomaly)
        emotional = EmotionalState(Prediction(value='Enojo', status='ok'))
        quality = AudioQuality(6, 6, 5, 16000, -20, 0)
        result = HybridEngine().cross_validate(acoustic, DemographicProfile(), physical, emotional, quality)
        self.assertIsNone(result.reliability_score)
        self.assertIsNone(result.emotional.stress_level)
        json.dumps(asdict(result), allow_nan=False)


class ServiceValidationTests(unittest.TestCase):
    def test_non_speech_is_rejected_before_loading_any_model(self):
        from src.core.analysis_service import AnalysisService
        service = AnalysisService()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.wav'
            t = np.arange(32000) / 16000
            samples = [np.zeros(32000), 0.1 * np.sin(2 * np.pi * 200 * t),
                       np.random.default_rng(7).normal(0, 0.05, 32000)]
            for sample in samples:
                sf.write(path, sample, 16000)
                with self.assertRaises(AudioValidationError):
                    service.analyze_path(path)
        self.assertTrue(all(model['status'] == 'not_loaded' for model in service.health()['models'].values()))


class ApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        from main import app
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test')

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_empty_and_oversized_uploads(self):
        response = await self.client.post('/api/analyze', files={'audio_file': ('x.wav', b'')})
        self.assertEqual(response.status_code, 400)
        with patch('src.api.routes.MAX_UPLOAD_BYTES', 10):
            response = await self.client.post('/api/analyze', files={'audio_file': ('x.wav', b'12345678901')})
        self.assertEqual(response.status_code, 413)

    async def test_validation_is_422_and_temp_file_is_always_removed(self):
        captured = []
        def analyze(path):
            captured.append(path)
            raise AudioValidationError('Graba varios segundos de habla.')
        service = SimpleNamespace(analyze_path=analyze)
        with patch('src.api.routes.get_service', return_value=service):
            response = await self.client.post('/api/analyze', files={'audio_file': ('x.wav', b'input')})
        self.assertEqual(response.status_code, 422)
        self.assertIn('habla', response.json()['detail'])
        self.assertFalse(captured[0].exists())

    async def test_inference_does_not_block_model_status_and_cleans_files(self):
        entered, release = Event(), Event()
        captured = []
        def analyze(path):
            captured.append(path)
            entered.set()
            release.wait(5)
            return {'raw_json': {'age': None}}
        service = SimpleNamespace(analyze_path=analyze, health=lambda: {'status': 'ready'})
        with patch('src.api.routes.get_service', return_value=service):
            pending = asyncio.create_task(self.client.post('/api/analyze', files={'audio_file': ('x.wav', b'input')}))
            try:
                self.assertTrue(await asyncio.to_thread(entered.wait, 3))
                response = await asyncio.wait_for(self.client.get('/api/models'), 2)
                self.assertEqual(response.json()['status'], 'ready')
            finally:
                release.set()
            self.assertEqual((await pending).status_code, 200)
        self.assertFalse(captured[0].exists())


if __name__ == '__main__':
    unittest.main()
