import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.ai_models.model_utils import asset
from config import MODEL_EMOTION, MODEL_LANG, MODEL_ACCENT

FILES = {
    MODEL_EMOTION: ['wav2vec2.ckpt', 'model.ckpt', 'label_encoder.txt'],
    MODEL_LANG: ['hyperparams.yaml', 'embedding_model.ckpt', 'classifier.ckpt', 'label_encoder.txt'],
    MODEL_ACCENT: ['wav2vec2.ckpt', 'model.ckpt', 'label_encoder.txt'],
    'facebook/wav2vec2-base': ['config.json', 'preprocessor_config.json'],
    'facebook/wav2vec2-large-xlsr-53': ['config.json', 'preprocessor_config.json'],
}

def download(item):
    repo, filename = item
    print(f'Descargando {repo}/{filename}', flush=True)
    result = asset(repo, filename)
    print(f'Listo {repo}/{filename}', flush=True)
    return result

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(download, [(repo, filename) for repo, files in FILES.items() for filename in files]))
