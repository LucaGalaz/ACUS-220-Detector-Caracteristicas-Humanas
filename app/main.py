"""
Punto de entrada principal para la aplicación ACUS-220 (FastAPI).
"""
import logging
import sys
import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.api.routes import router as api_router

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="ACUS-220 Voihunt API")

# Incluir rutas de API
app.include_router(api_router, prefix="/api")

# Montar frontend estático
public_dir = os.path.join(os.path.dirname(__file__), "src", "ui", "public")

# Servir index.html en la raíz
@app.get("/")
async def root():
    return FileResponse(
        os.path.join(public_dir, "index.html"),
        headers={"Cache-Control": "no-cache"},
    )

# Servir el resto de archivos (assets, css, js)
app.mount("/", StaticFiles(directory=public_dir), name="static")

def main():
    logger.info("Iniciando servidor ACUS-220 (FastAPI)...")
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__":
    main()
