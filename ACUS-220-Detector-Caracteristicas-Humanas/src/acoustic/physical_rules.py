"""
Reglas heurísticas para deducir estado físico basado en acústica.
"""
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import JITTER_THRESHOLD, SHIMMER_THRESHOLD, HNR_THRESHOLD
from src.core.data_models import AcousticFeatures, PhysicalState

logger = logging.getLogger(__name__)

class PhysicalRulesEngine:
    def __init__(self):
        pass

    def evaluate(self, acoustic: AcousticFeatures) -> PhysicalState:
        """
        Aplica reglas heurísticas sobre las características acústicas.
        :param acoustic: Objeto AcousticFeatures
        :return: Objeto PhysicalState
        """
        logger.info("Evaluando reglas físicas heurísticas.")
        
        smoker_prob = 0.0
        fatigue_prob = 0.0
        respiratory_anomaly = False
        notes = []
        
        # Evaluar tabaquismo o aspereza (Jitter alto, Shimmer alto, HNR bajo)
        if acoustic.jitter > JITTER_THRESHOLD:
            smoker_prob += 0.4
            notes.append(f"Jitter elevado ({acoustic.jitter:.3f}). Posible micro-inestabilidad vocal.")
        if acoustic.shimmer > SHIMMER_THRESHOLD:
            smoker_prob += 0.3
            notes.append(f"Shimmer elevado ({acoustic.shimmer:.3f}). Variación de amplitud anómala.")
        if acoustic.hnr > 0 and acoustic.hnr < HNR_THRESHOLD:
            smoker_prob += 0.3
            notes.append(f"HNR bajo ({acoustic.hnr:.2f} dB). Exceso de ruido espectral (posible disfonía/tabaquismo).")
            
        smoker_prob = min(1.0, smoker_prob)
        
        # Evaluar fatiga (Poca variación de tono y baja energía)
        if acoustic.f0_std > 0 and acoustic.f0_std < 10.0:
            fatigue_prob += 0.5
            notes.append("Desviación estándar de F0 baja. Posible habla monótona/fatiga.")
            
        if acoustic.energy_rms < 0.05 and acoustic.energy_rms > 0:
            fatigue_prob += 0.3
            notes.append("Energía RMS general baja.")
            
        fatigue_prob = min(1.0, fatigue_prob)
        
        # Anomalía respiratoria heurística simple: basado en HNR extremadamente bajo
        if acoustic.hnr > 0 and acoustic.hnr < (HNR_THRESHOLD - 5):
            respiratory_anomaly = True
            notes.append("Anomalía respiratoria detectada: HNR crítico.")
            
        return PhysicalState(
            smoker_prob=round(smoker_prob, 2),
            fatigue_prob=round(fatigue_prob, 2),
            respiratory_anomaly=respiratory_anomaly,
            notes=notes
        )
