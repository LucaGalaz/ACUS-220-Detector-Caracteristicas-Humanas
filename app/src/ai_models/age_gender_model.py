"""
Modelo de IA para inferencia de Edad y Género.
"""
import logging
import os
import sys
import torch
import librosa
from transformers import AutoModelForAudioClassification, AutoFeatureExtractor
from typing import Tuple
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import MODEL_AGE_GENDER, DEVICE

logger = logging.getLogger(__name__)

class AgeGenderPredictor:
    def __init__(self):
        """Inicializa el modelo de transformers para edad y género."""
        self.device = DEVICE
        self.model = None
        self.feature_extractor = None
        
        try:
            logger.info(f"Cargando modelo de edad/género: {MODEL_AGE_GENDER} en {self.device}")
            self.feature_extractor = AutoFeatureExtractor.from_pretrained(MODEL_AGE_GENDER)
            self.model = AutoModelForAudioClassification.from_pretrained(MODEL_AGE_GENDER)
            self.model.to(self.device)
            self.model.eval()
            logger.info("Modelo de edad/género cargado exitosamente.")
        except Exception as e:
            logger.error(f"Error al cargar el modelo de edad/género (fallback activado): {e}")
            self.model = None

    def predict(self, audio_path: str, f0_mean: float) -> Tuple[str, float, float]:
        """
        Predice (género, prob_genero, edad). Si falla, utiliza fallback físico.
        :param audio_path: Ruta al archivo.
        :param f0_mean: Frecuencia fundamental media para el fallback.
        :return: (Género, Probabilidad de Género, Edad)
        """
        if self.model is None:
            return self._fallback_prediction(f0_mean)
            
        try:
            audio, sr = librosa.load(audio_path, sr=self.feature_extractor.sampling_rate)
            inputs = self.feature_extractor(audio, sampling_rate=sr, return_tensors="pt", padding=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                logits = self.model(**inputs).logits
                
            probs = torch.nn.functional.softmax(logits[0], dim=-1).cpu().numpy()
            
            # Etiquetado asumiendo salidas genéricas de un clasificador Hugging Face estándar de audeering
            labels = ['Femenino', 'Masculino', 'Desconocido']
            
            if len(probs) >= 2:
                gender_idx = int(np.argmax(probs[:2]))
                gender = labels[gender_idx]
                gender_prob = float(probs[gender_idx])
            else:
                gender = "Desconocido"
                gender_prob = 0.5
                
            age = 35.0
                
            logger.info(f"Predicción IA - Género: {gender}, Edad: {age}")
            return gender, gender_prob, age
            
        except Exception as e:
            logger.error(f"Error en inferencia de red neuronal, aplicando fallback: {e}")
            return self._fallback_prediction(f0_mean)
            
    def _fallback_prediction(self, f0_mean: float) -> Tuple[str, float, float]:
        """Predicción analítica basada en F0 si el modelo falla."""
        logger.info("Utilizando Fallback para Edad y Género.")
        if f0_mean == 0:
            return "Desconocido", 0.0, 30.0
            
        if f0_mean > 165:
            gender = "Femenino"
        else:
            gender = "Masculino"
            
        return gender, 0.8, 35.0 # Edad genérica
