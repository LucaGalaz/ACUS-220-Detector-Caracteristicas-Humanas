import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = Path(os.environ.get('VOIHUNT_MODEL_DIR', BASE_DIR / 'models'))
SAMPLE_RATE = 16000
MIN_AUDIO_SECONDS = 1.0
MAX_AUDIO_SECONDS = 120.0
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
INFERENCE_SECONDS = 6.0
MAX_INFERENCE_SEGMENTS = 3
MODEL_AGE_GENDER = 'audeering/wav2vec2-large-robust-24-ft-age-gender'
MODEL_EMOTION = 'speechbrain/emotion-recognition-wav2vec2-IEMOCAP'
MODEL_LANG = 'speechbrain/lang-id-commonlanguage_ecapa'
MODEL_ACCENT = 'Jzuluaga/accent-id-commonaccent_xlsr-es-spanish'
DEVICE = os.environ.get('VOIHUNT_DEVICE', 'cpu')
TORCH_THREADS = int(os.environ.get('VOIHUNT_TORCH_THREADS', min(4, os.cpu_count() or 1)))
