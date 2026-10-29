import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import torch
from config import TORCH_THREADS
from src.ai_models.age_gender_model import AgeGenderPredictor
from src.ai_models.emotion_accent_model import EmotionAccentPredictor

if __name__ == '__main__':
    torch.set_num_threads(TORCH_THREADS)
    group = EmotionAccentPredictor()
    models = [AgeGenderPredictor(), group.lang_model, group.emotion_model, group.accent_model]
    for model in models:
        model.ensure_loaded()
        print(json.dumps(model.health(), ensure_ascii=False), flush=True)
    if not all(model.state == 'ready' for model in models):
        sys.exit(1)
