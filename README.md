# ACUS-220: Analizador y Detector de Características Humanas en la Voz (Voihunt)

**Asignatura:** ACUS220 - Acústica Computacional con Python

**Institución:** Universidad Austral de Chile (UACh)

**Integrantes:** Ian Cuevas, Marcelo Lara, Luca Galaz

**Docente:** Víctor Poblete

**Ayudante:** Carlos Duarte

**Fecha:** 28 de Octubre 2026 (Hito 2)

## 1. Descripción del Sistema

Este repositorio implementa una plataforma local de análisis acústico y biomecánico de la señal vocal orientada a la estimación exploratoria de atributos bio-psicosociales.

La arquitectura desacopla el procesamiento mediante una estrategia híbrida:

* **Rama Acústica Determinista:** Extrae descriptores biomecánicos fundamentales ($F_0$, Jitter, Shimmer, HNR) utilizando enlaces directos a las librerías `praat-parselmouth` y `openSMILE` para evaluar la estabilidad glótica y marcadores de fatiga/disfonía.

* **Rama de Inferencia Neuronal:** Emplea modelos acústicos preentrenados y codificadores contextuales (`wav2vec2`, arquitecturas `ECAPA-TDNN` y clasificadores basados en `SpeechBrain`) para tareas de estimación demográfica (edad, género) y clasificación de estados afectivos.

* **Motor Híbrido:** Realiza un contraste entre las salidas físicas y las predicciones estadísticas para reportar un índice de fiabilidad relativo del análisis.

## 2. Estructura del Repositorio

El proyecto concentra la lógica de negocio, servicios y controladores en el subdirectorio `app/`, manteniendo aislados los modelos descargados, las pruebas y los artefactos de documentación:

```
ACUS-220-Detector-Caracteristicas-Humanas/
├── app/
│   ├── src/
│   │   ├── acoustic/                # Extracción acústica y heurísticas físicas
│   │   │   ├── opensmile_extractor.py
│   │   │   ├── parselmouth_extractor.py
│   │   │   └── physical_rules.py
│   │   ├── ai_models/               # Modelos de inferencia neuronal (PyTorch/Transformers)
│   │   │   ├── age_gender_model.py
│   │   │   └── emotion_accent_model.py
│   │   ├── api/                     # Enrutamiento y controladores REST
│   │   │   └── routes.py
│   │   ├── core/                    # Estructuras de datos y motor híbrido
│   │   │   ├── data_models.py
│   │   │   └── hybrid_engine.py
│   │   ├── preprocessing/           # Normalización de señal y detección de actividad vocal (VAD)
│   │   │   └── audio_processor.py
│   │   └── ui/                      # Componentes de frontend e interfaz web
│   │       ├── components/          # Componentes de renderizado
│   │       ├── lib/                 # Utilidades TypeScript/JavaScript
│   │       ├── public/              # Archivos estáticos servidos por FastAPI (index.html, JS, CSS)
│   │       └── plots.py             # Generación de espectrogramas y formas de onda
│   ├── temp/                        # Imágenes temporales generadas (waveform.png, spectrogram.png)
│   ├── tests/                       # Pruebas automatizadas de integración
│   │   └── test_pipeline.py
│   ├── tmpdir_emotion/              # Pesos y configuración del modelo de emoción
│   ├── tmpdir_lang/                 # Pesos y configuración del modelo de identificación de idioma
│   ├── wav2vec2_checkpoints/        # Checkpoints locales de modelos basados en Wav2Vec2
│   ├── config.py                    # Parámetros y constantes de configuración del sistema
│   ├── main.py                      # Punto de entrada FastAPI y servidor Uvicorn
│   └── requirements.txt             # Dependencias del entorno Python
├── Documentacion/                   # Diagramas, esquemas y reportes técnicos
│   ├── Documentación_Acustica.pdf
│   └── flujo-acus220.png
├── LICENSE
└── README.md

```

## 3. Requisitos del Entorno

* **Python:** Versión 3.10.x recomendada.

* **Sistema Operativo:** Compatible con Windows 10/11, Linux y macOS.

## 4. Instalación y Configuración

1. **Clonar el repositorio:**

   ```
   git clone https://github.com/LucaGalaz/ACUS-220-Detector-Caracteristicas-Humanas.git
   cd ACUS-220-Detector-Caracteristicas-Humanas
   
   ```

2. **Crear y activar un entorno virtual:**

   * En Windows (PowerShell):

     ```
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     
     ```

   * En Linux / macOS:

     ```
     python3 -m venv venv
     source venv/bin/activate
     
     ```

3. **Instalar dependencias:**
   Navegar al directorio de la aplicación e instalar los requerimientos:

   ```
   cd app
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   
   ```

4. **Variables de entorno (Opcional):**
   Para suprimir advertencias por ausencia de enlaces simbólicos en la consola al descargar modelos de Hugging Face:

   * PowerShell:

     ```
     $env:HF_HUB_DISABLE_SYMLINKS_WARNING="1"
     
     ```

   * Bash:

     ```
     export HF_HUB_DISABLE_SYMLINKS_WARNING=1
     
     ```

## 5. Ejecución del Sistema

### Iniciar el Servidor Web

El servidor se ejecuta desde el directorio `app/`:

```
cd app
python main.py

```

El script inicializará el servidor `FastAPI` montado sobre `Uvicorn` en la dirección local:

```
http://127.0.0.1:8000

```

Al abrir esta URL en un navegador, la aplicación servirá la interfaz interactiva `Voihunt` desde `app/src/ui/public/index.html`.

### Endpoints Principales (API REST)

* `GET /`: Carga la interfaz web principal.

* `POST /api/analyze`: Recibe un archivo de audio en formato `.wav` (PCM 16-bit, frecuencia de muestreo recomendada $\ge 16000\text{ Hz}$) o captura por micrófono, ejecuta el preprocesamiento, la extracción acústica (Parselmouth/openSMILE) y la inferencia neuronal, retornando un objeto JSON estructurado con métricas, gráficos en `app/temp/` y el índice de fiabilidad.

* `GET /api/docs`: Documentación Swagger interactiva generada automáticamente por FastAPI.

## 6. Pruebas Automatizadas

El proyecto incluye pruebas de verificación para comprobar la integridad del flujo de procesamiento, la extracción de parámetros y el motor híbrido:

```
# Estando dentro del directorio app/
pytest -v tests/test_pipeline.py

```

## 7. Modelos y Referencias Técnicas

1. **Parselmouth (Praat):**

   Jadoul, Y., Thompson, B., & de Boer, B. (2018). *Introducing Parselmouth: A Python interface to Praat*. Journal of Phonetics, 71, 1–15.

2. **openSMILE / eGeMAPS:**

   Eyben, F., et al. (2016). *The Geneva Minimalistic Acoustic Parameter Set (GeMAPS) for Voice Research and Affective Computing*. IEEE Transactions on Affective Computing, 7(2), 190–202.

3. **SpeechBrain:**

   Ravanelli, M., et al. (2021). *SpeechBrain: A General-Purpose Speech Toolkit*. arXiv preprint arXiv:2106.04624.

4. **Wav2Vec 2.0:**

   Baevski, A., Zhou, Y., Mohamed, A., & Auli, M. (2020). *wav2vec 2.0: A framework for self-supervised learning of speech representations*. NeurIPS, 33, 12449–12460.

## 8. Declaración de Uso de Herramientas de IA

Se utilizaron herramientas de modelos de lenguaje basados en IA generativa como soporte asistencial en tareas de optimización de sintaxis en scripts de Python, consultas sobre la API de `transformers` y refinamiento de la documentación técnica. La concepción del motor híbrido, la estructuración del pipeline acústico, la depuración de dependencias locales y la toma de decisiones metodológicas fueron realizadas y verificadas por los autores del proyecto.
