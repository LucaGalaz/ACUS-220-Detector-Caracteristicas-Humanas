from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock
import uuid
import numpy as np
import soundfile as sf
import torch
from scipy.signal import welch
from config import TORCH_THREADS
from src.preprocessing.audio_processor import AudioProcessor, AudioValidationError
from src.acoustic.parselmouth_extractor import ParselmouthExtractor
from src.acoustic.opensmile_extractor import OpenSmileExtractor
from src.acoustic.physical_rules import PhysicalRulesEngine
from src.ai_models.age_gender_model import AgeGenderPredictor
from src.ai_models.emotion_accent_model import EmotionAccentPredictor
from src.core.data_models import AcousticFeatures, DemographicProfile, EmotionalState
from src.core.hybrid_engine import HybridEngine

LANGUAGES = {'Spanish': 'Español', 'English': 'Inglés', 'French': 'Francés', 'Italian': 'Italiano',
             'German': 'Alemán', 'Portuguese': 'Portugués', 'Arabic': 'Árabe', 'Japanese': 'Japonés',
             'Russian': 'Ruso', 'Catalan': 'Catalán', 'Basque': 'Euskera', 'Dutch': 'Neerlandés',
             'Chinese_China': 'Chino (China)', 'Chinese_Hongkong': 'Chino (Hong Kong)',
             'Chinese_Taiwan': 'Chino (Taiwán)'}


def label(value):
    if value is None:
        return 'No estimable'
    if value.startswith('RIOPLATENSE'):
        return 'Rioplatense'
    if value.startswith('ANDINOPACIFICO'):
        return 'Andino-pacífico'
    if value.startswith('CARIBE'):
        return 'Caribeño'
    if value.startswith('CHILENO'):
        return 'Chileno/Cuyo'
    if value.startswith('ESPANA SUR'):
        return 'Sur peninsular de España'
    if value == 'MEXICO':
        return 'Mexicano'
    return LANGUAGES.get(value, value)


def describe(prediction):
    def format_score(score):
        return f'similitud {score:.2f}' if prediction.details.get('score_type') == 'cosine_similarity' else f'puntaje {score:.0%}'
    if prediction.status == 'ok':
        score = f' ({format_score(prediction.score)})' if prediction.score is not None else ''
        return f'{label(prediction.value)}{score}'
    if prediction.status == 'uncertain' and prediction.distribution:
        candidate = max(prediction.distribution, key=prediction.distribution.get)
        return f'No concluyente (candidata: {label(candidate)}, {format_score(prediction.score)})'
    return f'No estimable. {prediction.reason}'


def measured(value, unit='', decimals=1, scale=1):
    return f'{value * scale:.{decimals}f}{unit}' if value is not None else 'No medible'


class AnalysisService:
    def __init__(self):
        torch.set_num_threads(TORCH_THREADS)
        self.lock = Lock()
        self.audio = AudioProcessor()
        self.praat = ParselmouthExtractor()
        self.smile = OpenSmileExtractor()
        self.physical = PhysicalRulesEngine()
        self.age_gender = AgeGenderPredictor()
        self.vocal = EmotionAccentPredictor()
        self.hybrid = HybridEngine()

    def health(self):
        return {'models': {name: model.health() for name, model in [
            ('age_gender', self.age_gender), ('language', self.vocal.lang_model),
            ('emotion', self.vocal.emotion_model), ('spanish_accent', self.vocal.accent_model)]},
            'unsupported': ['smoking_probability', 'fatigue_probability', 'respiratory_diagnosis', 'stress_diagnosis'],
            'emotion_training_language': 'English'}

    def analyze_path(self, path):
        with self.lock:
            audio, quality = self.audio.process_with_quality(path)
            with TemporaryDirectory(prefix='voihunt-analysis-') as directory:
                processed = Path(directory) / 'processed.wav'
                sf.write(processed, audio, quality.sample_rate, subtype='FLOAT')
                features = self.praat.extract_features(processed)
                if features['voiced_fraction'] < 0.1:
                    raise AudioValidationError('No se detectó suficiente habla con voz. Prueba una grabación clara, sin música de fondo.')
                frequencies, power = welch(audio, fs=quality.sample_rate, nperseg=1024)
                peak = int(np.argmax(power))
                concentration = float(power[max(0, peak - 2):peak + 3].sum() / max(power.sum(), 1e-20))
                if concentration > 0.97:
                    raise AudioValidationError('El archivo parece contener un tono sostenido, no habla suficiente para estimar atributos.')
                band = (frequencies >= 200) & (frequencies <= 4000)
                slope = float(np.polyfit(np.log10(frequencies[band]), 10 * np.log10(np.maximum(power[band], 1e-20)), 1)[0])
                smile = self.smile.extract_features(str(processed))
            acoustic = AcousticFeatures(**features, energy_rms=float(np.sqrt(np.mean(audio.astype(float) ** 2))),
                                        spectral_slope=slope, opensmile_features=smile)
            if not smile:
                acoustic.warnings.append('openSMILE no produjo métricas adicionales.')
            gender, age = self.age_gender.predict(audio, quality.sample_rate)
            emotion, language, accent = self.vocal.predict(audio, quality.sample_rate)
            demographic = DemographicProfile(gender, age, language, accent)
            physical = self.physical.evaluate(acoustic)
            emotional = EmotionalState(emotion, stress_level=None)
            result = self.hybrid.cross_validate(acoustic, demographic, physical, emotional, quality)
            raw = asdict(result)
            raw.update(schema_version=2, analysis_id=str(uuid.uuid4()),
                       created_at=datetime.now(timezone.utc).isoformat(), model_status=self.health())
            age_text = f'Aproximadamente {round(age.value)} años' if age.value is not None else describe(age)
            demographic_text = '\n'.join([f'Perfil vocal: {describe(gender)}', f'Edad estimada: {age_text}',
                                           f'Idioma: {describe(language)}', f'Acento regional: {describe(accent)}'])
            physical_text = '\n'.join([
                f'Tono medio: {measured(acoustic.f0_mean, " Hz")}',
                f'Variación tonal: {measured(acoustic.pitch_variation_semitones, " semitonos")}',
                f'Jitter: {measured(acoustic.jitter, "%", 2, 100)}',
                f'Shimmer: {measured(acoustic.shimmer, "%", 2, 100)}',
                f'Armonicidad (HNR): {measured(acoustic.hnr, " dB")}',
                'Tabaquismo, fatiga y salud respiratoria: no determinables con estas mediciones.'])
            emotion_text = '\n'.join([f'Emoción vocal: {describe(emotion)}',
                                      'Estrés: no evaluable con el modelo disponible.',
                                      'Estimación experimental fuera del inglés.' if emotion.details.get('outside_training_language')
                                      else 'La emoción predicha describe la expresión vocal, no el estado mental.'])
            diagnostic_text = '\n'.join([
                f'Duración: {quality.duration_seconds:.1f} s · audio activo: {quality.active_seconds:.1f} s',
                f'Nivel de entrada: {quality.rms_dbfs:.1f} dBFS · saturación: {quality.clipping_fraction:.1%}',
                f'Cobertura de voz periódica: {acoustic.voiced_fraction:.0%}',
                '\nObservaciones:', *[f'• {alert}' for alert in result.alerts]])
            return {'demographic_text': demographic_text, 'physical_text': physical_text,
                    'emotional_text': emotion_text, 'diagnostic_text': diagnostic_text, 'raw_json': raw}
