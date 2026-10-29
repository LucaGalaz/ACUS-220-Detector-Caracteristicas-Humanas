import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from math import gcd
from config import SAMPLE_RATE, MIN_AUDIO_SECONDS, MAX_AUDIO_SECONDS
from src.core.data_models import AudioQuality


class AudioValidationError(ValueError):
    pass


class AudioProcessor:
    def __init__(self, target_sr=SAMPLE_RATE):
        self.target_sr = target_sr

    def process_with_quality(self, file_path):
        try:
            info = sf.info(file_path)
            duration = info.frames / info.samplerate
            if not MIN_AUDIO_SECONDS <= duration <= MAX_AUDIO_SECONDS:
                raise AudioValidationError(f'Usa un audio de {MIN_AUDIO_SECONDS:g} a {MAX_AUDIO_SECONDS:g} segundos.')
            if not 8000 <= info.samplerate <= 192000 or not 1 <= info.channels <= 8:
                raise AudioValidationError('Frecuencia de muestreo o número de canales no admitido.')
            samples, sr = sf.read(file_path, dtype='float32', always_2d=True)
        except AudioValidationError:
            raise
        except Exception as error:
            raise AudioValidationError('No se pudo leer el archivo de audio.') from error
        if not np.isfinite(samples).all():
            raise AudioValidationError('El audio contiene muestras no válidas.')
        clipping = float(np.mean(np.abs(samples) >= 0.999))
        mono = samples.mean(axis=1)
        mono = mono - np.mean(mono)
        rms = float(np.sqrt(np.mean(mono.astype(np.float64) ** 2)))
        db = float(20 * np.log10(max(rms, 1e-12)))
        if db < -65:
            raise AudioValidationError('El audio está en silencio o es demasiado bajo. Acerca el micrófono y vuelve a grabar.')
        if sr != self.target_sr:
            divisor = gcd(sr, self.target_sr)
            mono = resample_poly(mono, self.target_sr // divisor, sr // divisor).astype(np.float32)

        size = self.target_sr // 50
        frames = np.pad(mono, (0, (-len(mono)) % size)).reshape(-1, size)
        frame_rms = np.sqrt(np.mean(frames.astype(np.float64) ** 2, axis=1))
        threshold = max(0.0003, float(np.max(frame_rms)) * 0.03)
        active = np.flatnonzero(frame_rms > threshold)
        active_seconds = len(active) * size / self.target_sr
        if active_seconds < 0.7:
            raise AudioValidationError('No hay suficiente audio activo. Graba varios segundos de habla clara.')
        padding = int(0.15 * self.target_sr)
        start = max(0, int(active[0]) * size - padding)
        end = min(len(mono), (int(active[-1]) + 1) * size + padding)
        trimmed = mono[start:end].astype(np.float32)
        warnings = []
        if active_seconds < 4:
            warnings.append('Grabación corta: usa al menos 6–10 segundos de habla para estimaciones más estables.')
        if clipping > 0.005:
            warnings.append('Hay saturación en la grabación; baja la ganancia del micrófono.')
        if db < -40:
            warnings.append('El nivel de grabación es bajo y puede reducir la calidad del análisis.')
        return trimmed, AudioQuality(duration, len(trimmed) / self.target_sr, active_seconds,
                                     self.target_sr, db, clipping, warnings)

    def process(self, file_path):
        return self.process_with_quality(file_path)[0]
