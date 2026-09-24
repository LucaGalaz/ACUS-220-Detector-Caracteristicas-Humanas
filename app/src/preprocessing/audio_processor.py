"""
Procesamiento de la señal de audio (Paso 1).
"""
import logging
import librosa
import numpy as np

logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self, target_sr: int = 16000, vad_threshold: float = 0.01):
        """
        Inicializa el procesador de audio.
        :param target_sr: Frecuencia de muestreo objetivo (Hz).
        :param vad_threshold: Umbral de energía RMS para recortes de silencio.
        """
        self.target_sr = target_sr
        self.vad_threshold = vad_threshold

    def process(self, file_path: str) -> np.ndarray:
        """
        Carga, remuestrea, aplica VAD y normaliza el audio.
        :param file_path: Ruta al archivo de audio.
        :return: Array de numpy con la señal de audio procesada.
        """
        try:
            logger.info(f"Cargando audio: {file_path}")
            # Cargar a canal mono y remuestrear
            y, sr = librosa.load(file_path, sr=self.target_sr, mono=True)
            
            # Recorte temporal por energía (VAD simplificado)
            y_trimmed = self._apply_vad(y)
            
            # Normalización min-max al rango [-1, 1]
            if len(y_trimmed) > 0:
                max_val = np.max(np.abs(y_trimmed))
                if max_val > 0:
                    y_normalized = y_trimmed / max_val
                else:
                    y_normalized = y_trimmed
            else:
                y_normalized = y
                
            logger.info("Audio procesado exitosamente.")
            return y_normalized.astype(np.float32)
        except Exception as e:
            logger.error(f"Error procesando audio: {e}")
            raise

    def _apply_vad(self, audio: np.ndarray) -> np.ndarray:
        """
        Aplica un Voice Activity Detection simple basado en energía RMS.
        :param audio: Señal de audio.
        :return: Señal de audio recortada.
        """
        # Calcular RMS por tramas
        frame_length = 2048
        hop_length = 512
        rms = librosa.feature.rms(y=audio, frame_length=frame_length, hop_length=hop_length)[0]
        
        # Encontrar índices donde la energía supera el umbral
        active_frames = np.where(rms > self.vad_threshold)[0]
        
        if len(active_frames) == 0:
            logger.warning("No se detectó actividad vocal significativa. Devolviendo audio original.")
            return audio
            
        start_frame = active_frames[0]
        end_frame = active_frames[-1]
        
        start_sample = start_frame * hop_length
        end_sample = min(len(audio), (end_frame * hop_length) + frame_length)
        
        return audio[start_sample:end_sample]
