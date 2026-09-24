# ACUS-220: Sistema Integral de Reconocimiento y Caracterización de Voz

Proyecto para la asignatura de Acústica Computacional. Implementa un pipeline híbrido de procesamiento digital de señales (DSP) y aprendizaje profundo (Deep Learning) para inferir características humanas a partir de la voz.

## Requisitos Previos
- Python 3.9+
- Sistema Operativo: Windows / Linux / macOS
- (Opcional) Compilador C++ para dependencias de openSMILE.

## Instalación y Despliegue

Sigue estos pasos en tu terminal:

1. **Clonar el repositorio y entrar a la carpeta:**
   ```bash
   cd ACUS-220-Detector-Caracteristicas-Humanas
   ```

2. **Crear y activar el Entorno Virtual (venv):**
   ```bash
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   # En Linux/macOS:
   source venv/bin/activate
   ```

3. **Instalar Dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la Aplicación:**
   ```bash
   python main.py
   ```
   La aplicación se abrirá localmente en `http://127.0.0.1:7860`.

## Consideraciones
La primera vez que analices un audio, los modelos de Inteligencia Artificial (Hugging Face / SpeechBrain) descargarán sus pesos (varios GB). Se requiere conexión a internet para esta descarga inicial. Si falla la red, el sistema utilizará reglas físicas de *fallback* para intentar deducir la información basándose en el F0 y energía.
