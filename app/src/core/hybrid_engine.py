"""
Motor Híbrido que consolida y cruza la información de los diferentes módulos.
"""
import logging
from typing import List
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.core.data_models import (
    AcousticFeatures, DemographicProfile, PhysicalState, 
    EmotionalState, HybridAnalysisResult
)

logger = logging.getLogger(__name__)

class HybridEngine:
    def __init__(self):
        pass
        
    def cross_validate(
        self, 
        acoustic: AcousticFeatures, 
        demographic: DemographicProfile, 
        physical: PhysicalState, 
        emotional: EmotionalState
    ) -> HybridAnalysisResult:
        """
        Ejecuta las validaciones cruzadas para generar el índice de fiabilidad.
        """
        logger.info("Iniciando validación cruzada híbrida.")
        alerts = []
        reliability_score = 100.0
        
        # 1. Validación F0 vs. Género
        if demographic.gender == 'Masculino' and acoustic.f0_mean > 175:
            alerts.append(f"Discrepancia: IA detecta Masculino pero F0 ({acoustic.f0_mean:.1f}Hz) es inusualmente alto.")
            reliability_score -= 15.0
        elif demographic.gender == 'Femenino' and acoustic.f0_mean > 0 and acoustic.f0_mean < 165:
            alerts.append(f"Discrepancia: IA detecta Femenino pero F0 ({acoustic.f0_mean:.1f}Hz) es inusualmente bajo.")
            reliability_score -= 15.0
            
        # 2. Validación Energía vs. Estrés/Emoción
        high_energy_emotions = ['Enojo / Ira', 'Alegría']
        if emotional.emotion in high_energy_emotions and acoustic.energy_rms < 0.05:
            alerts.append(f"Discrepancia: Emoción de alta energía ({emotional.emotion}) predicha, pero energía RMS ({acoustic.energy_rms:.3f}) es baja.")
            reliability_score -= 10.0
            
        # 3. Validación Estabilidad vs. Edad/Hábitos
        if demographic.age_group == 'Senior' and acoustic.jitter < 0.01:
            alerts.append("Nota: Perfil Senior con inusualmente alta estabilidad vocal (Jitter muy bajo).")
            # No bajamos reliability mucho por esto
            reliability_score -= 5.0
            
        # Calcular stress level basado en emoción IA y acústica
        if emotional.emotion in ['Enojo / Ira', 'Miedo'] or acoustic.energy_rms > 0.2:
            emotional.stress_level = 'Alto'
        elif acoustic.f0_std > 20 and acoustic.energy_rms > 0.1:
            emotional.stress_level = 'Medio'
        else:
            emotional.stress_level = 'Bajo'
            
        # Consolidar notas físicas y alertas
        alerts.extend(physical.notes)
        
        reliability_score = max(0.0, min(100.0, reliability_score))
        
        logger.info(f"Validación finalizada. Score de fiabilidad: {reliability_score}%")
        
        return HybridAnalysisResult(
            acoustic=acoustic,
            demographic=demographic,
            physical=physical,
            emotional=emotional,
            reliability_score=round(reliability_score, 1),
            alerts=alerts
        )
