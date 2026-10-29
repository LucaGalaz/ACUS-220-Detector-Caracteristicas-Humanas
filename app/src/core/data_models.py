from dataclasses import dataclass, field
from typing import Any


@dataclass
class Prediction:
    value: Any = None
    score: float | None = None
    status: str = 'unavailable'
    model: str | None = None
    reason: str = ''
    distribution: dict[str, float] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class AudioQuality:
    duration_seconds: float
    analyzed_seconds: float
    active_seconds: float
    sample_rate: int
    rms_dbfs: float
    clipping_fraction: float
    warnings: list[str] = field(default_factory=list)


@dataclass
class AcousticFeatures:
    f0_mean: float | None = None
    f0_std: float | None = None
    f0_min: float | None = None
    f0_max: float | None = None
    f1_mean: float | None = None
    f2_mean: float | None = None
    jitter: float | None = None
    shimmer: float | None = None
    hnr: float | None = None
    energy_rms: float | None = None
    spectral_slope: float | None = None
    voiced_fraction: float = 0.0
    pitch_variation_semitones: float | None = None
    opensmile_features: dict[str, float | None] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


@dataclass
class DemographicProfile:
    gender: Prediction = field(default_factory=Prediction)
    age: Prediction = field(default_factory=Prediction)
    language: Prediction = field(default_factory=Prediction)
    accent: Prediction = field(default_factory=Prediction)


@dataclass
class PhysicalState:
    smoker_prob: float | None = None
    fatigue_prob: float | None = None
    respiratory_anomaly: bool | None = None
    notes: list[str] = field(default_factory=list)


@dataclass
class EmotionalState:
    emotion: Prediction = field(default_factory=Prediction)
    stress_level: str | None = None


@dataclass
class HybridAnalysisResult:
    acoustic: AcousticFeatures
    demographic: DemographicProfile
    physical: PhysicalState
    emotional: EmotionalState
    quality: AudioQuality
    reliability_score: float | None = None
    alerts: list[str] = field(default_factory=list)
