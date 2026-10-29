import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock
from fastapi import APIRouter, UploadFile, File, HTTPException
from starlette.concurrency import run_in_threadpool
from config import MAX_UPLOAD_BYTES
from src.core.analysis_service import AnalysisService
from src.preprocessing.audio_processor import AudioValidationError

router = APIRouter()
logger = logging.getLogger(__name__)
_service = None
_initialization_lock = Lock()


def get_service():
    global _service
    with _initialization_lock:
        if _service is None:
            _service = AnalysisService()
        return _service


@router.get('/models')
def model_status():
    return get_service().health()


@router.post('/analyze')
async def analyze_audio(audio_file: UploadFile = File(...)):
    try:
        with TemporaryDirectory(prefix='voihunt-upload-') as directory:
            path = Path(directory) / 'input.audio'
            size = 0
            with path.open('wb') as output:
                while chunk := await audio_file.read(1024 * 1024):
                    size += len(chunk)
                    if size > MAX_UPLOAD_BYTES:
                        raise HTTPException(413, 'El audio supera el límite de 25 MB.')
                    output.write(chunk)
            if size == 0:
                raise HTTPException(400, 'El archivo de audio está vacío.')
            service = await run_in_threadpool(get_service)
            return await run_in_threadpool(service.analyze_path, path)
    except AudioValidationError as error:
        raise HTTPException(422, str(error)) from error
    except HTTPException:
        raise
    except Exception as error:
        logger.exception('No se pudo analizar el audio')
        raise HTTPException(500, 'No se pudo completar el análisis. Revisa el estado de los modelos e intenta de nuevo.') from error
    finally:
        await audio_file.close()
