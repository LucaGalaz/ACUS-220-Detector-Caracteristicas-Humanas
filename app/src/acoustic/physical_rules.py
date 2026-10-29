from src.core.data_models import PhysicalState


class PhysicalRulesEngine:
    def evaluate(self, acoustic):
        notes = ['Tabaquismo, fatiga y condiciones respiratorias no se determinan con estos indicadores acústicos.']
        if acoustic.jitter is not None or acoustic.shimmer is not None:
            notes.append('Jitter y shimmer dependen del fragmento y de las condiciones de grabación; no son diagnósticos.')
        return PhysicalState(notes=notes)
