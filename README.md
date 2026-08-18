# ACUS-220: Detector de Características Humanas a través de la Voz

Proyecto para la asignatura de Acústica Computacional. Sistema en Python orientado al análisis y la extracción automática de características biométricas, físicas y emocionales a partir de grabaciones de voz humana.

## Descripción del Proyecto

El sistema procesa archivos de audio o grabaciones en tiempo real para estimar diversos atributos del hablante. La arquitectura se plantea bajo un enfoque **híbrido**: combina el procesamiento digital de señales para la extracción de métricas físicas de la onda con modelos de aprendizaje profundo preentrenados para la clasificación automática. 

Los resultados de ambos módulos se cruzan en una capa de validación para contrastar las predicciones del modelo con la física del sonido, asignando un grado de confianza a las inferencias generadas.

## Características a Detectar

* **Perfil y Demografía:** Género, edad estimada y acento regional o nacionalidad.
* **Estado Físico y Hábitos:** Hábito de fumar, fatiga/somnolencia e indicadores de condiciones respiratorias o neurológicas.
* **Estado Mental y Emocional:** Nivel de estrés y clasificación de emociones primarias.

## Arquitectura y Flujo del Sistema

1. **Captura y Preprocesamiento:** Recepción de audio, estandarización de canal y remoción de silencios o ruido.
2. **Extracción Acústica Física:** Cálculo de parámetros físicos de la onda sonora (tono fundamental, resonancias, energía y variabilidad fónica).
3. **Inferencia con Modelos Preentrenados:** Procesamiento del audio mediante redes neuronales especializadas para la clasificación de atributos de alto nivel.
4. **Cruce y Validación (Motor Híbrido):** Script de integración que compara los valores físicos obtenidos con las predicciones de los modelos para verificar consistencia y detectar discrepancias.
5. **Visualización:** Interfaz gráfica para la presentación de métricas físicas, espectrogramas y tarjetas de diagnóstico validado.


## LINKS
https://mozilladatacollective.com/datasets/cmqi28y2v004imf076oh7e5zs
