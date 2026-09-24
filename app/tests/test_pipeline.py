"""
Pruebas unitarias básicas para asegurar que el pipeline no falle con audios válidos.
"""
import unittest
import numpy as np
import os
import soundfile as sf
import tempfile
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.preprocessing.audio_processor import AudioProcessor
from src.core.data_models import AcousticFeatures
from src.acoustic.physical_rules import PhysicalRulesEngine

class TestPipeline(unittest.TestCase):
    def setUp(self):
        # Crear un audio falso (tono puro de 200 Hz)
        self.sr = 16000
        t = np.linspace(0, 1.0, self.sr)
        self.y = 0.5 * np.sin(2 * np.pi * 200 * t)
        
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_audio_path = os.path.join(self.temp_dir.name, "test_tone.wav")
        sf.write(self.test_audio_path, self.y, self.sr)
        
    def tearDown(self):
        self.temp_dir.cleanup()

    def test_audio_processor(self):
        proc = AudioProcessor(target_sr=16000)
        y_proc = proc.process(self.test_audio_path)
        self.assertTrue(len(y_proc) > 0)
        self.assertTrue(np.max(np.abs(y_proc)) <= 1.0)
        
    def test_physical_rules(self):
        engine = PhysicalRulesEngine()
        fake_features = AcousticFeatures(
            f0_mean=200.0, f0_std=5.0, f0_min=195.0, f0_max=205.0,
            f1_mean=500.0, f2_mean=1500.0,
            jitter=0.03, shimmer=0.06, hnr=10.0,
            energy_rms=0.1, spectral_slope=-1.0
        )
        result = engine.evaluate(fake_features)
        self.assertTrue(result.smoker_prob > 0.0)
        
if __name__ == '__main__':
    unittest.main()
