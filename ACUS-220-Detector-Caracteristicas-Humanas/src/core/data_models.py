"""
Modelos de datos para transitar información en el pipeline.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class AcousticFeatures:
    f0_mean: float
    f0_std: float
    f0_min: float
    f0_max: float
    f1_mean: float
    f2_mean: float
    jitter: float
    shimmer: float
    hnr: float
    energy_rms: float
    spectral_slope: float
    opensmile_features: Dict[str, float] = field(default_factory=dict)

@dataclass
class DemographicProfile:
    gender: str  # 'Masculino' | 'Femenino' | 'Desconocido'
    gender_prob: float
    age_group: str  # 'Joven', 'Adulto', 'Senior'
    age_value: float
    language_accent: str
    language_prob: float

@dataclass
class PhysicalState:
    smoker_prob: float
    fatigue_prob: float
    respiratory_anomaly: bool
    notes: List[str] = field(default_factory=list)

@dataclass
class EmotionalState:
    emotion: str
    emotion_prob: float
    stress_level: str # 'Bajo', 'Medio', 'Alto'

@dataclass
class HybridAnalysisResult:
    acoustic: AcousticFeatures
    demographic: DemographicProfile
    physical: PhysicalState
    emotional: EmotionalState
    reliability_score: float
    alerts: List[str] = field(default_factory=list)
