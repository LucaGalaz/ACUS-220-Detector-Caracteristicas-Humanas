import logging
import parselmouth
from parselmouth.praat import call
import numpy as np

logger = logging.getLogger(__name__)


def finite(value):
    return float(value) if np.isfinite(value) else None


class ParselmouthExtractor:
    def extract_features(self, audio_path):
        result = {key: None for key in ['f0_mean', 'f0_std', 'f0_min', 'f0_max', 'f1_mean',
                                       'f2_mean', 'jitter', 'shimmer', 'hnr', 'pitch_variation_semitones']}
        result.update(voiced_fraction=0.0, warnings=[])
        sound = parselmouth.Sound(str(audio_path))
        try:
            pitch = sound.to_pitch_ac(time_step=0.01, pitch_floor=60, pitch_ceiling=600)
            contour = pitch.selected_array['frequency']
            voiced = contour > 0
            f0 = contour[voiced]
            result['voiced_fraction'] = float(np.mean(voiced)) if len(voiced) else 0.0
            if len(f0):
                result.update(f0_mean=float(np.mean(f0)), f0_std=float(np.std(f0)),
                              f0_min=float(np.quantile(f0, 0.05)), f0_max=float(np.quantile(f0, 0.95)),
                              pitch_variation_semitones=float(np.std(12 * np.log2(f0))))
                formant = sound.to_formant_burg(time_step=0.02)
                times = pitch.xs()[voiced][::3]
                for number in [1, 2]:
                    values = [formant.get_value_at_time(number, float(time)) for time in times]
                    valid = [value for value in values if np.isfinite(value)]
                    result[f'f{number}_mean'] = float(np.mean(valid)) if valid else None


                changes = np.diff(np.r_[False, voiced, False].astype(int))
                runs = list(zip(np.flatnonzero(changes == 1), np.flatnonzero(changes == -1)))
                first, last = max(runs, key=lambda run: run[1] - run[0])
                begin, end = float(pitch.xs()[first]), float(pitch.xs()[last - 1])
                if end - begin >= 0.4:
                    fragment = sound.extract_part(from_time=begin, to_time=end, preserve_times=False)
                    points = call(fragment, 'To PointProcess (periodic, cc)', 60, 600)
                    result['jitter'] = finite(call(points, 'Get jitter (local)', 0, 0, 0.0001, 0.02, 1.3))
                    result['shimmer'] = finite(call([fragment, points], 'Get shimmer (local)', 0, 0, 0.0001, 0.02, 1.3, 1.6))
            harmonicity = sound.to_harmonicity_cc(time_step=0.01, minimum_pitch=60)
            values = harmonicity.values.flatten()
            values = values[np.isfinite(values) & (values > -100)]
            result['hnr'] = float(np.mean(values)) if len(values) else None
        except Exception as error:
            logger.exception('Medición acústica parcial')
            result['warnings'].append(f'Algunas métricas acústicas no se pudieron medir: {type(error).__name__}.')
        if result['voiced_fraction'] < 0.1:
            result['warnings'].append('No se detectó suficiente voz periódica; las estimaciones del hablante se omiten.')
        return result
