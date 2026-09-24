"""
Modelo de IA para inferencia de Emoción e Idioma/Acento.
"""
import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import MODEL_EMOTION, MODEL_LANG, DEVICE

logger = logging.getLogger(__name__)

class EmotionAccentPredictor:
    def __init__(self):
        """Inicializa los modelos de SpeechBrain."""
        self.device = "cpu" # Forzamos CPU para evitar dependencias complejas de GPU en SpeechBrain local
        self.emotion_model = None
        self.lang_model = None
        
        try:
            from speechbrain.inference.interfaces import foreign_class
            logger.info(f"Cargando modelo de emociones: {MODEL_EMOTION}")
            # Intentar usar foreign_class genérico (requiere custom_interface.py en el repo remoto)
            self.emotion_model = foreign_class(
                source=MODEL_EMOTION, 
                pymodule_file="custom_interface.py", 
                classname="CustomEncoderWav2vec2Classifier", 
                savedir="tmpdir_emotion"
            )
        except Exception as e:
            logger.error(f"No se pudo cargar modelo de emoción específico, intentando genérico: {e}")
            try:
                from speechbrain.inference.classifiers import EncoderClassifier
                self.emotion_model = EncoderClassifier.from_hparams(source=MODEL_EMOTION, savedir="tmpdir_emotion")
            except Exception as e2:
                logger.error(f"Fallo definitivo en carga de modelo de emoción: {e2}")
                self.emotion_model = None

        try:
            from speechbrain.inference.classifiers import EncoderClassifier
            logger.info(f"Cargando modelo de idioma: {MODEL_LANG}")
            self.lang_model = EncoderClassifier.from_hparams(source=MODEL_LANG, savedir="tmpdir_lang")
        except Exception as e:
            logger.error(f"Error al cargar modelo de idioma: {e}")
            self.lang_model = None

    def predict(self, audio_path: str, energy_rms: float, f0_std: float) -> tuple:
        """
        Predice Emoción y Acento. Aplica fallback en caso de error.
        :param audio_path: Ruta al archivo.
        :param energy_rms: Energía para el fallback.
        :param f0_std: Varianza de F0 para el fallback.
        :return: (Emocion, Prob_Emocion, Idioma, Prob_Idioma)
        """
        emotion, emotion_prob = self._predict_emotion(audio_path, energy_rms, f0_std)
        lang, lang_prob = self._predict_lang(audio_path)
        
        return emotion, emotion_prob, lang, lang_prob
        
    def _predict_emotion(self, audio_path: str, energy_rms: float, f0_std: float):
        if self.emotion_model is not None:
            try:
                out_prob, score, index, text_lab = self.emotion_model.classify_file(audio_path)
                return str(text_lab[0]), float(score[0].item())
            except Exception as e:
                logger.error(f"Error prediciendo emoción, fallback: {e}")
                
        # Fallback de emoción
        logger.info("Fallback de Emoción activado.")
        if energy_rms > 0.15 and f0_std > 30:
            return "Enojo / Ira", 0.7
        elif energy_rms < 0.05 and f0_std < 10:
            return "Tristeza / Fatiga", 0.7
        else:
            return "Neutral", 0.6
            
    def _predict_lang(self, audio_path: str):
        if self.lang_model is not None:
            try:
                out_prob, score, index, text_lab = self.lang_model.classify_file(audio_path)
                return str(text_lab[0]), float(score[0].item())
            except Exception as e:
                logger.error(f"Error prediciendo idioma, fallback: {e}")
                
        # Fallback de idioma
        logger.info("Fallback de Idioma activado.")
        return "Desconocido (Fallback)", 0.0
