from src.core.data_models import HybridAnalysisResult


class HybridEngine:
    def cross_validate(self, acoustic, demographic, physical, emotional, quality):
        alerts = list(quality.warnings) + list(acoustic.warnings)
        for name, prediction in [('Perfil vocal', demographic.gender), ('Edad', demographic.age),
                                 ('Idioma', demographic.language), ('Acento', demographic.accent),
                                 ('Emoción', emotional.emotion)]:
            if prediction.status != 'ok':
                alerts.append(f'{name}: {prediction.reason or "resultado no concluyente"}')
        if emotional.emotion.details.get('outside_training_language'):
            alerts.append('Emoción: modelo entrenado en inglés; fuera de ese idioma el resultado es experimental.')
        alerts.append('Los puntajes de clasificación son salidas del modelo, no porcentajes de exactitud comprobada.')
        alerts.append('No hay una fiabilidad global calibrada para esta grabación.')
        return HybridAnalysisResult(acoustic, demographic, physical, emotional, quality,
                                    reliability_score=None, alerts=alerts)
