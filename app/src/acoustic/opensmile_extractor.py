import logging
import opensmile
from typing import Dict
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class OpenSmileExtractor:
    def __init__(self):
        try:
            self.smile = opensmile.Smile(
                feature_set=opensmile.FeatureSet.eGeMAPSv02,
                feature_level=opensmile.FeatureLevel.Functionals,
            )
            logger.info("openSMILE inicializado.")
        except Exception as e:
            logger.error(f"Error al inicializar openSMILE: {e}")
            self.smile = None

    def extract_features(self, audio_path: str) -> Dict[str, float]:
        features = {}
        if self.smile is None:
            logger.warning("openSMILE no disponible. Retornando dict vacío.")
            return features

        try:
            logger.info(f"openSMILE procesando: {audio_path}")
            df: pd.DataFrame = self.smile.process_file(audio_path)


            if not df.empty:
                row = df.iloc[0].to_dict()
                for k, v in row.items():
                    if pd.isna(v) or np.isnan(v):
                        features[k] = None
                    else:
                        features[k] = float(v) if np.isfinite(v) else None

            logger.info("Características openSMILE extraídas con éxito.")
            return features
        except Exception as e:
            logger.error(f"Error en OpenSmileExtractor: {e}")
            return features
