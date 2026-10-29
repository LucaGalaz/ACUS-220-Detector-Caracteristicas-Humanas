from pathlib import Path
import shutil
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from transformers import Wav2Vec2Config, Wav2Vec2Model, Wav2Vec2FeatureExtractor
from config import MODEL_EMOTION, MODEL_LANG, MODEL_ACCENT, MODEL_DIR, DEVICE
from src.core.data_models import Prediction
from src.ai_models.model_utils import (ModelResource, asset, windows, exact_state,
                                      classification, cosine_classification, read_labels)

EMOTIONS = {'neu': 'Neutral', 'hap': 'Alegría/entusiasmo', 'sad': 'Tristeza', 'ang': 'Enojo'}


class VocalClassifier(ModelResource):
    def __init__(self, model_id, base_id):
        super().__init__(model_id)
        self.base_id = base_id

    def load(self):
        config = Wav2Vec2Config.from_json_file(asset(self.base_id, 'config.json'))
        config.apply_spec_augment = False
        self.processor = Wav2Vec2FeatureExtractor.from_pretrained(
            str(Path(asset(self.base_id, 'preprocessor_config.json')).parent))
        wrapper = nn.Module()
        wrapper.model = Wav2Vec2Model(config)
        state = torch.load(asset(self.model_id, 'wav2vec2.ckpt'), map_location='cpu', weights_only=True)
        exact_state(wrapper, state)
        self.encoder = wrapper.model.to(DEVICE).eval()
        self.labels = read_labels(asset(self.model_id, 'label_encoder.txt'))
        head = torch.load(asset(self.model_id, 'model.ckpt'), map_location='cpu', weights_only=True)
        if self.model_id == MODEL_ACCENT:
            expected = {'0.linear.w.weight', '0.linear.w.bias', '0.linear_0.w.weight',
                        '0.linear_0.w.bias', '1.w.weight'}
            if set(head) != expected:
                raise ValueError('Arquitectura del modelo de acentos inesperada.')
            self.classifier = nn.Sequential(nn.Linear(config.hidden_size, config.hidden_size), nn.GELU(),
                                            nn.Linear(config.hidden_size, config.hidden_size), nn.GELU(),
                                            nn.Linear(config.hidden_size, len(self.labels), bias=False))
            exact_state(self.classifier, {'0.weight': head['0.linear.w.weight'], '0.bias': head['0.linear.w.bias'],
                                         '2.weight': head['0.linear_0.w.weight'], '2.bias': head['0.linear_0.w.bias'],
                                         '4.weight': head['1.w.weight']})
        elif set(head) == {'0.w.weight'}:
            self.classifier = nn.Linear(config.hidden_size, len(self.labels), bias=False)
            exact_state(self.classifier, {'weight': head['0.w.weight']})
        else:
            raise ValueError(f'Cabeza de clasificación inesperada: {list(head)}')
        self.classifier.to(DEVICE).eval()

    def infer(self, audio, sr=16000):
        if not self.ensure_loaded():
            return self.unavailable()
        outputs = []
        try:
            for part in windows(audio, sr):
                values = self.processor(part, sampling_rate=sr, return_tensors='pt').input_values.to(DEVICE)
                with torch.inference_mode():
                    encoded = self.encoder(values).last_hidden_state
                    normalized = F.layer_norm(encoded, encoded.shape[1:])
                    logits = self.classifier(normalized.mean(dim=1))
                    outputs.append(logits[0].softmax(-1).cpu().numpy())
            return classification(np.mean(outputs, axis=0), self.labels, self.model_id,
                                  minimum=0.55, details={'segments': len(outputs)})
        except Exception as error:
            return Prediction(status='error', model=self.model_id, reason=str(error))


class LanguageClassifier(ModelResource):
    def __init__(self):
        super().__init__(MODEL_LANG)

    def load(self):
        from speechbrain.inference.classifiers import EncoderClassifier
        from speechbrain.utils.fetching import LocalStrategy
        directory = MODEL_DIR / 'language'
        directory.mkdir(parents=True, exist_ok=True)
        for filename in ['hyperparams.yaml', 'embedding_model.ckpt', 'classifier.ckpt', 'label_encoder.txt']:
            source = Path(asset(self.model_id, filename))
            destination = directory / filename
            if source.resolve() != destination.resolve() and not destination.exists():
                shutil.copyfile(source, destination)
        self.model = EncoderClassifier.from_hparams(
            source=str(directory), savedir=str(directory), local_strategy=LocalStrategy.COPY,
            overrides={'pretrained_path': directory.as_posix()}, run_opts={'device': DEVICE})
        self.labels = read_labels(directory / 'label_encoder.txt')
        self.model.hparams.label_encoder.expect_len(len(self.labels))

    def infer(self, audio, sr=16000):
        if not self.ensure_loaded():
            return self.unavailable()
        try:
            outputs = []
            for part in windows(audio, sr):
                with torch.inference_mode():
                    values, *_ = self.model.classify_batch(torch.from_numpy(part.copy()).unsqueeze(0).to(DEVICE))
                outputs.append(values.cpu().numpy().reshape(-1))
            result = cosine_classification(np.mean(outputs, axis=0), self.labels, self.model_id)
            result.details['segments'] = len(outputs)
            return result
        except Exception as error:
            return Prediction(status='error', model=self.model_id, reason=str(error))


class EmotionAccentPredictor:
    def __init__(self):
        self.emotion_model = VocalClassifier(MODEL_EMOTION, 'facebook/wav2vec2-base')
        self.lang_model = LanguageClassifier()
        self.accent_model = VocalClassifier(MODEL_ACCENT, 'facebook/wav2vec2-large-xlsr-53')

    def predict(self, audio, sr=16000):
        if len(audio) / sr < 2:
            def missing(model):
                return Prediction(status='insufficient_audio', model=model, reason='Se necesitan al menos 2 segundos de habla.')
            return missing(MODEL_EMOTION), missing(MODEL_LANG), missing(MODEL_ACCENT)
        language = self.lang_model.infer(audio, sr)
        emotion = self.emotion_model.infer(audio, sr)
        emotion.details['training_language'] = 'English'
        emotion.details['outside_training_language'] = language.value != 'English'
        if emotion.value is not None:
            emotion.value = EMOTIONS.get(emotion.value, emotion.value)
        emotion.distribution = {EMOTIONS.get(key, key): value for key, value in emotion.distribution.items()}
        if language.value == 'Spanish' and len(audio) / sr >= 4:
            accent = self.accent_model.infer(audio, sr)
            accent.details['scope'] = 'Seis variedades del español; no determina nacionalidad.'
        elif language.value == 'Spanish':
            accent = Prediction(status='insufficient_audio', model=MODEL_ACCENT,
                                reason='Se necesitan al menos 4 segundos de habla para acento.')
        else:
            accent = Prediction(status='not_applicable', model=MODEL_ACCENT,
                                reason='El modelo de acentos requiere español identificado con suficiente certeza.')
        return emotion, language, accent
