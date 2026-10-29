# Voihunt — ACUS-220

Aplicación de análisis de voz para Acústica Computacional. Permite grabar o
subir un audio, revisar los resultados y descargar el reporte en JSON.

## Qué analiza

- Edad aproximada y perfil vocal.
- Idioma y seis variedades regionales del español.
- Expresión vocal: neutral, enojo, alegría/entusiasmo y tristeza.
- Tono, variación tonal, jitter, shimmer, armonicidad y métricas openSMILE.

Las estimaciones pueden fallar o quedar como no concluyentes. El modelo de
emociones está entrenado en inglés; en otros idiomas el resultado es experimental.
No se evalúan tabaquismo, fatiga, estrés ni enfermedades respiratorias.

## Ejecutar

Se necesita Python y un entorno con las dependencias de `app/requirements.txt`.
Si ya existe el entorno del proyecto, desde la raíz:

```powershell
app/venv/Scripts/python.exe -m pip install -r app/requirements.txt
app/venv/Scripts/python.exe app/scripts/download_models.py
app/venv/Scripts/python.exe app/scripts/prepare_models.py
app/venv/Scripts/python.exe app/main.py
```

La aplicación queda en http://127.0.0.1:8000. Los modelos se guardan en
`app/models/`; los pesos y el entorno virtual no se incluyen en Git.

## Estructura

- `app/main.py`: servidor FastAPI.
- `app/src/api/`: carga de archivos y estado de modelos.
- `app/src/preprocessing/`: lectura y validación de audio.
- `app/src/acoustic/`: mediciones con Praat y openSMILE.
- `app/src/ai_models/`: carga e inferencia de los modelos.
- `app/src/core/`: análisis completo y estructura del reporte.
- `app/src/ui/public/`: interfaz HTML, CSS y JavaScript.
- `app/scripts/`: descarga, preparación y comprobación de modelos.
- `app/tests/`: pruebas del backend.

La interfaz se sirve directamente desde FastAPI y no requiere Node ni un build.

## Pruebas

```powershell
app/venv/Scripts/python.exe -m pip install -r app/requirements-dev.txt
app/venv/Scripts/python.exe -m unittest discover -s app/tests -v
app/venv/Scripts/python.exe app/scripts/validate_models.py
```

## Documentación

- [Análisis de voz, modelos y limitaciones](Documentacion/analisis-voz.md).
- [Interfaz, temas y grabación](Documentacion/inicio-y-temas.md).
- [Fondo de puntos](Documentacion/fondo-puntos.md).

## Datos de referencia

- [Mozilla Data Collective](https://mozilladatacollective.com/datasets/cmqi28y2v004imf076oh7e5zs).
- [Spoken Language Identification](https://www.kaggle.com/datasets/toponowicz/spoken-language-identification).
