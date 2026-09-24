"""
Funciones de visualizacion usando matplotlib (Voihunt - ACUS-220).
"""
import matplotlib.pyplot as plt
import numpy as np
import librosa
import librosa.display
import os

def create_waveform_plot(y: np.ndarray, sr: int, output_path: str = "temp/waveform.png"):
    """Crea y guarda el grafico de forma de onda con fondo transparente."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fig = plt.figure(figsize=(8, 2.2), facecolor='none')
    ax = fig.add_subplot(111)
    ax.set_facecolor('none')
    
    # Color valido de matplotlib (no CSS rgba)
    librosa.display.waveshow(y, sr=sr, alpha=0.8, color='#ffffff', ax=ax)
    
    ax.tick_params(colors='#888888')
    for spine in ax.spines.values():
        spine.set_edgecolor('#888888')
    ax.set_title("Forma de Onda", color='#888888', fontsize=9, pad=2)
    
    plt.tight_layout(pad=0.5)
    plt.savefig(output_path, transparent=True)
    plt.close(fig)
    return output_path

def create_spectrogram_plot(y: np.ndarray, sr: int, output_path: str = "temp/spectrogram.png"):
    """Crea y guarda el espectrograma con contorno de F0 superpuesto."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fig = plt.figure(figsize=(8, 2.2), facecolor='none')
    ax = fig.add_subplot(111)
    ax.set_facecolor('none')
    
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=8000)
    S_dB = librosa.power_to_db(S, ref=np.max)
    
    librosa.display.specshow(S_dB, x_axis='time', y_axis='mel', sr=sr, fmax=8000, ax=ax, cmap='viridis', alpha=0.7)
    
    # F0 contour
    f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), sr=sr)
    times = librosa.times_like(f0, sr=sr)
    ax.plot(times, f0, color='#00e5ff', linewidth=1.5, alpha=0.9)
    
    ax.tick_params(colors='#888888')
    for spine in ax.spines.values():
        spine.set_edgecolor('#888888')
    ax.set_title("Espectrograma + F0", color='#888888', fontsize=9, pad=2)
    
    plt.tight_layout(pad=0.5)
    plt.savefig(output_path, transparent=True)
    plt.close(fig)
    return output_path
