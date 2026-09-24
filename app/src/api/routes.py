import tempfile
import os
import json
import logging
import numpy as np
import soundfile as sf
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from src.preprocessing.audio_processor import AudioProcessor
from src.acoustic.parselmouth_extractor import ParselmouthExtractor
from src.acoustic.opensmile_extractor import OpenSmileExtractor
from src.acoustic.physical_rules import PhysicalRulesEngine
from src.ai_models.age_gender_model import AgeGenderPredictor
from src.ai_models.emotion_accent_model import EmotionAccentPredictor
from src.core.hybrid_engine import HybridEngine
from src.core.data_models import AcousticFeatures, DemographicProfile, EmotionalState

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize ML models and extractors globally as None
audio_proc = None
pars_ext = None
smile_ext = None
phys_engine = None
age_gen_model = None
emo_acc_model = None
hybrid_engine = None

def init_models():
    global audio_proc, pars_ext, smile_ext, phys_engine, age_gen_model, emo_acc_model, hybrid_engine
    if audio_proc is None:
        logger.info("Inicializando modelos de Inteligencia Artificial (openSMILE, Wav2Vec2)...")
        audio_proc = AudioProcessor()
        pars_ext = ParselmouthExtractor()
        smile_ext = OpenSmileExtractor()
        phys_engine = PhysicalRulesEngine()
        age_gen_model = AgeGenderPredictor()
        emo_acc_model = EmotionAccentPredictor()
        hybrid_engine = HybridEngine()
        logger.info("Todos los modelos han sido cargados exitosamente.")

@router.post("/analyze")
async def analyze_audio(audio_file: UploadFile = File(...)):
    if audio_proc is None:
        init_models()
    
    if not audio_file:
        raise HTTPException(status_code=400, detail="No audio file provided.")
    
    # Create temp file
    fd, temp_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    
    try:
        # Save uploaded file
        with open(temp_path, "wb") as f:
            content = await audio_file.read()
            f.write(content)
            
        logger.info(f"Processing audio: {temp_path}")
        
        y_proc = audio_proc.process(temp_path)
        
        fd_proc, proc_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd_proc)
        sf.write(proc_path, y_proc, audio_proc.target_sr)

        p_feat = pars_ext.extract_features(proc_path)
        s_feat = smile_ext.extract_features(proc_path)

        energy = float(np.sqrt(np.mean(y_proc**2))) if len(y_proc) > 0 else 0.0
        acoustics = AcousticFeatures(
            f0_mean=p_feat["f0_mean"], f0_std=p_feat["f0_std"],
            f0_min=p_feat["f0_min"],  f0_max=p_feat["f0_max"],
            f1_mean=p_feat["f1_mean"], f2_mean=p_feat["f2_mean"],
            jitter=p_feat["jitter"],  shimmer=p_feat["shimmer"],
            hnr=p_feat["hnr"], energy_rms=energy,
            spectral_slope=0.0, opensmile_features=s_feat,
        )

        physical = phys_engine.evaluate(acoustics)

        gender, g_prob, age = age_gen_model.predict(proc_path, acoustics.f0_mean)
        age_group = "Joven" if age < 30 else ("Adulto" if age < 55 else "Senior")

        emotion, e_prob, lang, l_prob = emo_acc_model.predict(
            proc_path, acoustics.energy_rms, acoustics.f0_std
        )

        demographic = DemographicProfile(
            gender=gender, gender_prob=g_prob,
            age_group=age_group, age_value=age,
            language_accent=lang, language_prob=l_prob,
        )
        emotional = EmotionalState(
            emotion=emotion, emotion_prob=e_prob, stress_level="Desconocido"
        )

        result = hybrid_engine.cross_validate(acoustics, demographic, physical, emotional)

        demo_out = (
            f"Género: {result.demographic.gender} ({result.demographic.gender_prob:.1%})\n"
            f"Edad Estimada: {result.demographic.age_value:.1f} años ({result.demographic.age_group})\n"
            f"Idioma/Acento: {result.demographic.language_accent} ({result.demographic.language_prob:.1%})"
        )
        phys_out = (
            f"Prob. Tabaquismo: {result.physical.smoker_prob:.1%}\n"
            f"Prob. Fatiga: {result.physical.fatigue_prob:.1%}\n"
            f"Anomalía Respiratoria: {'Sí' if result.physical.respiratory_anomaly else 'No'}"
        )
        emo_out = (
            f"Emoción: {result.emotional.emotion} ({result.emotional.emotion_prob:.1%})\n"
            f"Nivel de Estrés: {result.emotional.stress_level}"
        )
        alerts_text = (
            "\n".join([f"- {a}" for a in result.alerts])
            if result.alerts else "Sin anomalías físicas detectadas."
        )
        diag_out = (
            f"Índice de Fiabilidad: {result.reliability_score}%\n\n"
            f"Observaciones:\n{alerts_text}"
        )
        
        raw_json = {
            "reliability": result.reliability_score,
            "demographic": {"gender": result.demographic.gender, "age": result.demographic.age_value},
            "emotional": {"emotion": result.emotional.emotion, "stress": result.emotional.stress_level},
            "alerts": result.alerts,
        }
        
        # Cleanup temp files
        if os.path.exists(proc_path): os.remove(proc_path)

        return JSONResponse(content={
            "demographic_text": demo_out,
            "physical_text": phys_out,
            "emotional_text": emo_out,
            "diagnostic_text": diag_out,
            "raw_json": raw_json
        })

    except Exception as e:
        logger.error(f"Error procesando audio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
