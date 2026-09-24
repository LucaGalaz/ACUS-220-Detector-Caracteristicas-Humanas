"""
Configuración global para ACUS-220.
"""
import os

# Rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "temp")

os.makedirs(TEMP_DIR, exist_ok=True)

# Parámetros de Audio
SAMPLE_RATE = 16000
VAD_ENERGY_THRESHOLD = 0.01  # Umbral RMS para Voice Activity Detection

# Parámetros Físicos Biológicos (F0 en Hz)
F0_MALE_MIN = 85
F0_MALE_MAX = 180
F0_FEMALE_MIN = 165
F0_FEMALE_MAX = 255

# Umbrales Heurísticos
JITTER_THRESHOLD = 0.02  # 2%
SHIMMER_THRESHOLD = 0.05 # 5%
HNR_THRESHOLD = 15.0     # dB, por debajo es señal con ruido/aspereza

# Modelos Hugging Face / SpeechBrain
MODEL_AGE_GENDER = "audeering/wav2vec2-large-robust-24-ft-age-gender"
MODEL_EMOTION = "speechbrain/emotion-recognition-wav2vec2-IEMOCAP"
MODEL_LANG = "speechbrain/lang-id-commonlanguage_ecapa"

# Configuración de ejecución
DEVICE = "cpu" # 'cuda' si está disponible
try:
    import torch
    if torch.cuda.is_available():
        DEVICE = "cuda"
except ImportError:
    pass
