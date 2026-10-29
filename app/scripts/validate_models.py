import json
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.core.analysis_service import AnalysisService
from src.ai_models.model_utils import asset
from config import MODEL_EMOTION, MODEL_LANG, MODEL_ACCENT, BASE_DIR

SAMPLES = [(MODEL_LANG, 'example-it.wav'), (MODEL_LANG, 'example-fr.wav'),
           (MODEL_EMOTION, 'anger.wav'), (MODEL_ACCENT, 'data/mexico.wav'),
           (MODEL_ACCENT, 'data/caribe-cuba-colombia.wav')]

if __name__ == '__main__':
    service = AnalysisService()
    reports = []
    for repo, filename in SAMPLES:
        started = time.perf_counter()
        try:
            response = service.analyze_path(asset(repo, filename))
            reports.append({'sample': f'{repo}/{filename}', 'seconds': round(time.perf_counter() - started, 2), **response})
            raw = response['raw_json']
            print(json.dumps({'sample': filename, 'seconds': reports[-1]['seconds'],
                              'demographic': raw['demographic'], 'emotional': raw['emotional']}, ensure_ascii=False), flush=True)
        except Exception as error:
            reports.append({'sample': filename, 'error': str(error)})
            print(json.dumps(reports[-1], ensure_ascii=False), flush=True)
    (BASE_DIR / 'temp').mkdir(exist_ok=True)
    (BASE_DIR / 'temp' / 'model-validation.json').write_text(json.dumps(reports, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    if any('error' in report for report in reports):
        sys.exit(1)
    by_name = {report['sample'].split('/')[-1]: report['raw_json'] for report in reports}
    ages = [report['raw_json']['demographic']['age']['value'] for report in reports
            if report['raw_json']['demographic']['age']['value'] is not None]
    assert max(ages) - min(ages) > 5, 'La edad debe depender de la señal.'
    assert by_name['anger.wav']['emotional']['emotion']['value'] == 'Enojo'
    assert by_name['anger.wav']['demographic']['language']['value'] == 'English'
    for filename in ['mexico.wav', 'caribe-cuba-colombia.wav']:
        assert by_name[filename]['demographic']['language']['value'] == 'Spanish'
    assert by_name['mexico.wav']['demographic']['accent']['value'] == 'MEXICO'
    assert by_name['caribe-cuba-colombia.wav']['demographic']['accent']['value'].startswith('CARIBE')
    for report in reports:
        raw = report['raw_json']
        assert raw['physical']['smoker_prob'] is None and raw['emotional']['stress_level'] is None
        assert raw['reliability_score'] is None
    print('PASS: edad variable; enojo/inglés; español y dos acentos distintos; sin resultados clínicos ni fiabilidad inventados.', flush=True)
