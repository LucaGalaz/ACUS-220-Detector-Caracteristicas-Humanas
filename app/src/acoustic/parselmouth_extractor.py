"""
Extracción de características usando Praat-Parselmouth.
"""
import logging
import parselmouth
from parselmouth.praat import call
import numpy as np
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

class ParselmouthExtractor:
    def __init__(self):
        """Inicializa el extractor de características físicas."""
        pass

    def extract_features(self, audio_path: str) -> Dict[str, float]:
        """
        Extrae F0, formantes, jitter, shimmer y HNR usando Praat.
        :param audio_path: Ruta al archivo de audio.
        :return: Diccionario con las características extraídas.
        """
        features = {
            'f0_mean': 0.0, 'f0_std': 0.0, 'f0_min': 0.0, 'f0_max': 0.0,
            'f1_mean': 0.0, 'f2_mean': 0.0,
            'jitter': 0.0, 'shimmer': 0.0, 'hnr': 0.0
        }
        try:
            logger.info(f"Parselmouth procesando: {audio_path}")
            sound = parselmouth.Sound(audio_path)
            
            # 1. Extracción de F0 (Pitch)
            pitch = call(sound, "To Pitch", 0.0, 75, 600) # time_step, pitch_floor, pitch_ceiling
            f0_values = pitch.selected_array['frequency']
            f0_values = f0_values[f0_values > 0] # Filtrar frames sin pitch (silencio)
            
            if len(f0_values) > 0:
                features['f0_mean'] = float(np.mean(f0_values))
                features['f0_std'] = float(np.std(f0_values))
                features['f0_min'] = float(np.min(f0_values))
                features['f0_max'] = float(np.max(f0_values))
                
            # 2. Formantes (F1, F2)
            formant = call(sound, "To Formant (burg)", 0.0, 5, 5500, 0.025, 50)
            f1_list = []
            f2_list = []
            for t in np.arange(0, sound.xmax, 0.01):
                f1 = call(formant, "Get value at time", 1, t, 'Hertz', 'Linear')
                f2 = call(formant, "Get value at time", 2, t, 'Hertz', 'Linear')
                if not np.isnan(f1): f1_list.append(f1)
                if not np.isnan(f2): f2_list.append(f2)
                
            if f1_list: features['f1_mean'] = float(np.mean(f1_list))
            if f2_list: features['f2_mean'] = float(np.mean(f2_list))
            
            # 3. Jitter y Shimmer
            pointProcess = call(sound, "To PointProcess (periodic, cc)", 75, 600)
            features['jitter'] = call(pointProcess, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
            features['shimmer'] = call([sound, pointProcess], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
            
            if np.isnan(features['jitter']): features['jitter'] = 0.0
            if np.isnan(features['shimmer']): features['shimmer'] = 0.0
            
            # 4. HNR (Harmonics-to-Noise Ratio)
            harmonicity = call(sound, "To Harmonicity (cc)", 0.01, 75, 0.1, 1.0)
            hnr = call(harmonicity, "Get mean", 0, 0)
            if not np.isnan(hnr):
                features['hnr'] = float(hnr)
                
            logger.info("Características físicas extraídas con éxito.")
            return features
        except Exception as e:
            logger.error(f"Error en ParselmouthExtractor: {e}")
            return features
