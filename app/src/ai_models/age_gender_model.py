import numpy as np
from pathlib import Path
import torch
from torch import nn
from safetensors.torch import load_file
from transformers import Wav2Vec2Config, Wav2Vec2FeatureExtractor, Wav2Vec2Model
from config import MODEL_AGE_GENDER, DEVICE
from src.core.data_models import Prediction
from src.ai_models.model_utils import ModelResource, asset, windows, exact_state, classification


class RegressionClassificationHead(nn.Module):
    def __init__(self, config, outputs):
        super().__init__()
        self.dense = nn.Linear(config.hidden_size, config.hidden_size)
        self.dropout = nn.Dropout(config.final_dropout)
        self.out_proj = nn.Linear(config.hidden_size, outputs)

    def forward(self, features):
        return self.out_proj(self.dropout(torch.tanh(self.dense(self.dropout(features)))))


class TrainedAgeGenderNetwork(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.wav2vec2 = Wav2Vec2Model(config)
        self.age = RegressionClassificationHead(config, 1)
        self.gender = RegressionClassificationHead(config, 3)

    def forward(self, audio):
        pooled = self.wav2vec2(audio).last_hidden_state.mean(dim=1)
        return self.age(pooled), self.gender(pooled).softmax(dim=-1)


class AgeGenderPredictor(ModelResource):
    def __init__(self):
        super().__init__(MODEL_AGE_GENDER)

    def load(self):
        config = Wav2Vec2Config.from_json_file(asset(self.model_id, 'config.json'))
        self.labels = [config.id2label[index] for index in range(3)]
        if set(self.labels) != {'female', 'male', 'child'}:
            raise ValueError('Etiquetas de edad/género inesperadas.')
        self.processor = Wav2Vec2FeatureExtractor.from_pretrained(
            str(Path(asset(self.model_id, 'preprocessor_config.json')).parent))
        self.model = TrainedAgeGenderNetwork(config)
        exact_state(self.model, load_file(asset(self.model_id, 'model.safetensors')))
        self.model.to(DEVICE).eval()

    def predict(self, audio, sr=16000):
        if len(audio) / sr < 3:
            missing = lambda: Prediction(status='insufficient_audio', model=self.model_id,
                                         reason='Se necesitan al menos 3 segundos de habla para edad y perfil vocal.')
            return missing(), missing()
        if not self.ensure_loaded():
            return self.unavailable(), self.unavailable()
        ages, scores = [], []
        try:
            for part in windows(audio, sr):
                values = self.processor(part, sampling_rate=sr, return_tensors='pt').input_values.to(DEVICE)
                with torch.inference_mode():
                    age, gender = self.model(values)
                ages.append(float(age.item()) * 100)
                scores.append(gender[0].cpu().numpy())
            if not ages or not np.isfinite(ages).all() or any(not 0 <= age <= 110 for age in ages):
                raise ValueError('La regresión de edad no produjo valores válidos.')
            spread = float(np.ptp(ages))
            age = Prediction(value=round(float(np.median(ages)), 1), status='ok', model=self.model_id,
                             details={'segment_estimates_years': ages, 'segment_spread_years': round(spread, 1),
                                      'approximate': True, 'calibrated_error_interval': None})
            if spread > 20:
                age.value, age.status, age.reason = None, 'uncertain', 'La edad cambia demasiado entre fragmentos.'
            labels = [{'female': 'Voz femenina', 'male': 'Voz masculina', 'child': 'Voz infantil'}[label] for label in self.labels]
            gender = classification(np.mean(scores, axis=0), labels, self.model_id,
                                    details={'segments': len(scores), 'attribute': 'perfil vocal, no identidad de género'})
            return gender, age
        except Exception as error:
            return (Prediction(status='error', model=self.model_id, reason=str(error)),
                    Prediction(status='error', model=self.model_id, reason=str(error)))
