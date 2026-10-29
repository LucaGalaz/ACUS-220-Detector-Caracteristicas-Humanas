import ast
import logging
from pathlib import Path
import numpy as np
from huggingface_hub import hf_hub_download, try_to_load_from_cache
from config import MODEL_DIR, INFERENCE_SECONDS, MAX_INFERENCE_SEGMENTS
from src.core.data_models import Prediction

logger = logging.getLogger(__name__)


def asset(repo, filename):
    for directory in [MODEL_DIR / 'hub', None]:
        existing = try_to_load_from_cache(repo, filename, cache_dir=directory)
        if isinstance(existing, str) and Path(existing).is_file():
            return existing
    return hf_hub_download(repo, filename, cache_dir=MODEL_DIR / 'hub')


def windows(audio, sr=16000):
    size = int(INFERENCE_SECONDS * sr)
    if len(audio) <= size:
        return [audio]
    starts = np.linspace(0, len(audio) - size, min(MAX_INFERENCE_SEGMENTS, int(np.ceil(len(audio) / size)))).astype(int)
    return [audio[start:start + size] for start in starts
            if np.sqrt(np.mean(audio[start:start + size].astype(np.float64) ** 2)) > 0.0003]


def probabilities(values):
    values = np.asarray(values, dtype=float).reshape(-1)
    if not np.isfinite(values).all() or len(values) < 2:
        raise ValueError('Salida de clasificación no válida.')
    if np.all(values >= 0) and np.isclose(values.sum(), 1, atol=1e-3):
        return values / values.sum()
    scores = np.exp(values - np.max(values))
    return scores / scores.sum()


def classification(values, labels, model, minimum=0.6, margin=0.15, details=None):
    scores = probabilities(values)
    if len(scores) != len(labels):
        raise ValueError('Las etiquetas no coinciden con las salidas del modelo.')
    order = np.argsort(scores)[::-1]
    score = float(scores[order[0]])
    accepted = score >= minimum and score - float(scores[order[1]]) >= margin
    return Prediction(value=labels[order[0]] if accepted else None,
                      score=score, status='ok' if accepted else 'uncertain', model=model,
                      reason='' if accepted else 'El modelo no separa con claridad las alternativas.',
                      distribution=dict(zip(labels, map(float, scores))),
                      details=details or {})


def cosine_classification(values, labels, model):
    scores = np.asarray(values, dtype=float).reshape(-1)
    if len(scores) != len(labels) or not np.isfinite(scores).all() or np.max(np.abs(scores)) > 1.001:
        raise ValueError('Similitudes de idioma no válidas.')
    order = np.argsort(scores)[::-1]
    score = float(scores[order[0]])
    gap = score - float(scores[order[1]])
    accepted = score >= 0.3 and gap >= 0.05
    return Prediction(value=labels[order[0]] if accepted else None, score=score,
                      status='ok' if accepted else 'uncertain', model=model,
                      reason='' if accepted else 'Las similitudes entre idiomas no son suficientemente distintas.',
                      distribution=dict(zip(labels, map(float, scores))),
                      details={'score_type': 'cosine_similarity', 'top_margin': gap,
                               'acceptance_similarity': 0.3, 'acceptance_margin': 0.05})


def exact_state(module, state):
    target = module.state_dict()
    converted = {}
    for key, value in state.items():
        if key not in target:
            for old, new in [('.weight_g', '.parametrizations.weight.original0'),
                             ('.weight_v', '.parametrizations.weight.original1')]:
                if key.endswith(old) and key[:-len(old)] + new in target:
                    key = key[:-len(old)] + new
                    break
        converted[key] = value
    module.load_state_dict(converted, strict=True)


def read_labels(filename):
    labels = {}
    for line in Path(filename).read_text(encoding='utf-8').splitlines():
        if line.startswith('==='):
            break
        if ' => ' in line:
            label, index = line.rsplit(' => ', 1)
            labels[int(index)] = ast.literal_eval(label)
    return [labels[index] for index in range(len(labels))]


class ModelResource:
    def __init__(self, model_id):
        self.model_id = model_id
        self.state = 'not_loaded'
        self.error = None

    def ensure_loaded(self):
        if self.state == 'not_loaded':
            try:
                self.load()
                self.state = 'ready'
                logger.info('Modelo listo: %s', self.model_id)
            except Exception as error:
                self.state = 'unavailable'
                self.error = f'{type(error).__name__}: {error}'
                logger.exception('Modelo no disponible: %s', self.model_id)
        return self.state == 'ready'

    def unavailable(self):
        return Prediction(model=self.model_id, reason='El modelo no está disponible. Consulta el estado de modelos.',
                          details={'error': self.error})

    def health(self):
        return {'model': self.model_id, 'status': self.state, 'error': self.error}
