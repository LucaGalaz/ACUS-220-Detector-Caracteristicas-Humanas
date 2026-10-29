# Análisis de voz: correcciones y límites

## Errores encontrados

- La edad se asignaba literalmente a `35.0`. El cargador genérico de
  clasificación no correspondía al checkpoint de audeering, que tiene una
  cabeza de regresión de edad y otra de tres clases vocales.
- En Windows, SpeechBrain fallaba con `WinError 1314` al intentar crear
  enlaces simbólicos. Emoción e idioma no llegaban a cargar sus pesos.
- Tras esos fallos se inventaba una emoción por umbrales de energía y tono;
  la alternativa más frecuente era `Neutral`, con un supuesto 60 %.
- Los porcentajes de tabaquismo y fatiga eran sumas de constantes sobre
  jitter, shimmer y HNR, sin modelo entrenado ni calibración.
- El estrés se decidía por volumen y variación de tono. La fiabilidad global
  empezaba siempre en 100 %, aunque los modelos hubieran fallado.
- El idioma se presentaba como si también fuera el acento regional.
- La normalización al pico modificaba el volumen utilizado por esas reglas.
- Los valores no medibles de Praat/openSMILE se convertían en ceros, que podían
  parecer mediciones válidas.

## Funcionamiento actual

| Dato | Implementación | Alcance |
| --- | --- | --- |
| Edad | Cabeza de regresión entrenada de audeering, salida multiplicada por 100 | Estimación aproximada; no edad verificada |
| Perfil vocal | Cabeza entrenada con clases female/male/child, leyendo sus etiquetas reales | Describe voz, no identidad de género |
| Idioma | ECAPA CommonLanguage de SpeechBrain, 45 clases | Devuelve similitudes coseno, no porcentajes de confianza |
| Acento | XLSR CommonAccent para español, con su clasificador GELU completo | Seis variedades regionales; no determina nacionalidad |
| Emoción vocal | Wav2vec2 IEMOCAP: neutral, enojo, alegría/entusiasmo y tristeza | Entrenado en inglés; en español se marca experimental |
| Acústica | Praat y openSMILE | Tono, variación en semitonos, formantes, jitter, shimmer, HNR, energía y pendiente espectral |
| Tabaquismo, fatiga, estrés y enfermedad respiratoria | Sin clasificador validado en este proyecto | No evaluables; sus valores se exportan como `null` |

Las variedades de acento disponibles son mexicano, caribeño, andino-pacífico,
rioplatense, chileno/Cuyo y sur peninsular de España. El clasificador regional
solo se utiliza si se identifica español y hay al menos cuatro segundos.

No se ha entrenado un modelo nuevo ni medido una mejora de precisión general
en un conjunto independiente. Se repararon la carga, la arquitectura y la
interpretación de los modelos publicados. Un resultado variable no garantiza
que sea correcto para cualquier hablante, idioma, micrófono o entorno.

### Carga de modelos

`model_utils.asset` reutiliza primero la caché del proyecto y después la caché
de Hugging Face existente. Los nuevos archivos quedan bajo `app/models/`,
fuera de Git. Edad, emoción y acento cargan todos sus tensores con comprobación
estricta: una cabeza ausente o incompatible no se sustituye por pesos aleatorios.

La inferencia de emoción/acento está implementada localmente con los pesos
publicados; no ejecuta el `custom_interface.py` descargado. Esto evita los
enlaces simbólicos y los imports antiguos del paquete SpeechBrain. Además,
el YAML público de acentos omite las dos capas GELU que sí existen en su
checkpoint; se recuperó la arquitectura de la receta de entrenamiento del autor.
El modelo de idioma utiliza archivos locales y `LocalStrategy.COPY`.

Los archivos de voz del usuario se procesan localmente en el servidor. Las
descargas iniciales son de pesos/configuraciones públicas; el audio no se envía
a Hugging Face. Una vez preparados los modelos, la caché permite trabajar sin red.

### Entrada y calidad

- Máximo 25 MB y entre 1 y 120 segundos; para estimaciones útiles, grabar
  al menos 6–10 segundos de habla de una sola persona.
- Se comprueban formato, duración, canales, valores no finitos, silencio,
  volumen y saturación antes de cargar modelos.
- Se remuestrea a 16 kHz y mono, conservando la amplitud. Solo se recortan los
  bordes inactivos; no se pegan fragmentos eliminando las pausas interiores.
- La detección de actividad por energía no se confunde con un VAD aprendido.
  Se comprueba cobertura de voz periódica y se rechazan ruido sin voz y tonos
  casi puros. Estos controles no son un detector universal de habla/música.
- Jitter y shimmer se miden sobre un tramo continuo de voz, evitando enlazar
  pulsos a través de silencios. En habla continua no deben interpretarse como
  diagnóstico ni como sustitutos de una prueba de vocal sostenida.
- Lo que no se puede medir queda como `null`, con observaciones.

La inferencia usa hasta tres ventanas de seis segundos repartidas por el
audio, para limitar memoria y cubrir más de un fragmento. Se promedian las
salidas de clasificación y se toma la mediana de las edades. Si la edad cambia
más de veinte años entre ventanas, se abstiene. La dispersión se exporta como
variación entre fragmentos, no como intervalo de confianza calibrado.

### Puntajes y resultados ausentes

Las clasificaciones con alternativas cercanas se muestran como «No
concluyente», conservando candidatos y puntajes. El perfil vocal requiere
puntaje mínimo 0,60 y margen 0,15; emoción/acento, 0,55 y 0,15. El idioma
conserva las similitudes originales y requiere máximo al menos 0,30 y margen
0,05. Son umbrales de abstención de ingeniería, no precisión medida.

Los puntajes normalizados de un clasificador tampoco son porcentajes de
acierto comprobado. No se calcula una fiabilidad global ficticia. Si un modelo
falla, se informa el motivo y no se devuelve edad 35, emoción neutral ni
ninguna otra respuesta de reserva.

## API e interfaz

- `POST /api/analyze` conserva los cuatro campos de texto para las tarjetas.
- La inferencia y carga pesada se ejecutan en un trabajador, sin bloquear el
  bucle de FastAPI. La inicialización y ejecución de modelos están protegidas
  contra solicitudes concurrentes que duplicarían memoria.
- `GET /api/models` muestra `not_loaded`, `ready` o `unavailable`, con el error
  de carga cuando corresponda. Un estado `not_loaded` no significa fallo:
  los modelos se cargan al necesitarlos.
- Archivo vacío: HTTP 400; exceso de tamaño: 413; audio inadecuado: 422 con
  explicación. Los temporales se eliminan también si falla el análisis.
- La interfaz muestra esos errores junto a la grabación o archivo seleccionado
  y permite reintentar. No analiza automáticamente al pulsar Stop.
- Se corrigió la cuantización de muestras negativas al convertir a WAV.

El JSON ahora utiliza `schema_version: 2` e incluye todas las predicciones,
sus estados, puntajes, candidatos, modelos y motivos; además de las métricas,
calidad de entrada y limitaciones. Los estados distinguen `ok`, `uncertain`,
`unavailable`, `error`, `insufficient_audio` y `not_applicable`. Los datos de
salud no soportados y `reliability_score` son `null`.

## Preparar y ejecutar

Desde la raíz del repositorio, utilizando el entorno del proyecto:

```powershell
app/venv/Scripts/python.exe -m pip install -r app/requirements-dev.txt
app/venv/Scripts/python.exe app/scripts/download_models.py
app/venv/Scripts/python.exe app/scripts/prepare_models.py
app/venv/Scripts/python.exe app/main.py
```

No hace falta ejecutar como administrador. La primera preparación descarga
varios GB y los modelos ocupan varios GB de RAM. Se recomienda un único proceso
del servidor; varios workers duplican los pesos. `VOIHUNT_MODEL_DIR`,
`VOIHUNT_DEVICE` y `VOIHUNT_TORCH_THREADS` permiten ajustar directorio, dispositivo
y CPU. El límite predeterminado es de cuatro hilos Torch.

Probado en el entorno existente con Python 3.14.3, Torch 2.13 CPU,
Transformers 5.16.1 y SpeechBrain 1.1.1. Las versiones de Torch y Torchaudio
deben corresponder al mismo entorno y plataforma al instalar desde cero.

## Comprobación reproducible

```powershell
app/venv/Scripts/python.exe -m unittest discover -s app/tests -v
app/venv/Scripts/python.exe app/scripts/validate_models.py
```

Las 18 pruebas unitarias pasan sin descargar pesos. Cubren señales inválidas,
ganancia, remuestreo, valores ausentes, uso de las cabezas de edad/perfil vocal,
puntajes, abstención, límites, rechazo de tonos/ruido, limpieza y API concurrente.

La integración utiliza cinco audios públicos de los propios autores. Resultados
observados en este equipo (prueba de funcionamiento, no benchmark independiente):

| Ejemplo | Edad devuelta | Idioma | Acento | Emoción |
| --- | --- | --- | --- | --- |
| CommonLanguage `example-it.wav` | 48,4 | No concluyente; mejor candidato italiano | No aplicable | Neutral, experimental |
| CommonLanguage `example-fr.wav` | No estimable: audio corto | No estimable: audio corto | No estimable | No estimable |
| IEMOCAP `anger.wav` | 51,1 | Inglés | No aplicable | Enojo |
| CommonAccent `data/mexico.wav` | 35,3 | Español | Mexicano | Enojo, experimental |
| CommonAccent `data/caribe-cuba-colombia.wav` | 34,0 | Español | Caribeño | Alegría/entusiasmo, experimental |

Las edades y emociones de los audios de idioma/acento no tienen verdad de
referencia en esta comprobación. La tabla acredita que las salidas dependen del
audio y que los ejemplos etiquetados de idioma/acento/enojo se procesan; no
acredita exactitud de edad ni precisión emocional en español. Se guardan los
reportes completos en `app/temp/model-validation.json` para inspección local.

También se comprobó la app desde un navegador contra el servidor FastAPI real:
subida del ejemplo mexicano, resultado en cuatro tarjetas, descarga idéntica
del JSON completo, una segunda voz inglesa con otra edad y emoción de enojo,
y rechazo de silencio con HTTP 422 y conservación del archivo para reintentar.
El endpoint de estado respondió durante la inferencia y los cuatro modelos
quedaron `ready`. Se revisaron los temas claro/oscuro y el diseño móvil.

## Fuentes y licencias de los modelos

- [audeering: arquitectura de dos cabezas, escala de edad y licencia CC BY-NC-SA 4.0](https://huggingface.co/audeering/wav2vec2-large-robust-24-ft-age-gender).
- [SpeechBrain IEMOCAP: cuatro emociones, entrenamiento en inglés, Apache 2.0](https://huggingface.co/speechbrain/emotion-recognition-wav2vec2-IEMOCAP).
- [CommonLanguage ECAPA: identificación de idiomas, Apache 2.0](https://huggingface.co/speechbrain/lang-id-commonlanguage_ecapa).
- [CommonAccent español: seis variedades, MIT y limitaciones publicadas](https://huggingface.co/Jzuluaga/accent-id-commonaccent_xlsr-es-spanish).
- [Receta original del clasificador regional: capas GELU y orden de pooling](https://github.com/JuanPZuluaga/accent-recog-slt2022/blob/main/CommonAccent/accent_id/hparams/train_w2v2.yaml).
- [Praat: medición e interpretación de shimmer](https://praat.org/manual/Voice_3__Shimmer.html).

La licencia MIT del código del proyecto no cambia las licencias de los pesos.
