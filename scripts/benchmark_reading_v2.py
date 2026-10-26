"""Frozen eight-paper first pass. Record failures; never repair or publish."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend import reading_v2 as reading, store, settings

CASES = ['rag', 'adaptive-dcs-somp', 'shannon', 'lyrics', 'moral-machine',
         'simulation-argument', 'generative-ai-work', 'macroeconomics-ai']
PROTECTED = ['documents', 'messages', 'patches', 'library', 'memories']


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def protected():
    with store.connection() as db:
        return {table: {'count': db.execute(f'SELECT count(*) FROM {table}').fetchone()[0],
                        'sha256': hashlib.sha256(store.encode([list(row) for row in db.execute(f'SELECT * FROM {table} ORDER BY id')]).encode()).hexdigest()}
                for table in PROTECTED}


def implementation():
    paths = sorted({p for pattern in ['backend/*.py', 'frontend/reading-v2-runtime.js',
                   'frontend/src/*.tsx', 'frontend/src/*.css', 'agents/skills/reading-v2-*/SKILL.md',
                   'scripts/render-reading-math.mjs'] for p in store.ROOT.glob(pattern)})
    return {str(p.relative_to(store.ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def run(case, out):
    started = time.monotonic()
    did = 'pdf-' + case['sha256'][:16]
    value = {'case': case['id'], 'title': case['title'], 'pages': case['page_count'],
             'document_id': did, 'status': 'running', 'started_at': reading.now()}
    target = out / (case['id'] + '.json')
    try:
        with store.connection() as db:
            doc = store.get_document(db, did)
        if not doc or doc['status'] != 'ready':
            raise ValueError('Canonical document is not ready')
        if hashlib.sha256(Path(doc['file_path']).read_bytes()).hexdigest() != case['sha256']:
            raise ValueError('PDF hash does not match frozen corpus')
        value['base_hash'] = reading.document_hash(doc)
        edition = reading.create(did)
        value['edition'] = edition['id']
        value['folder'] = str(reading.folder(edition['id']))
        save(target, value)
        print(f"START {case['id']} {edition['id']}", flush=True)
        result = reading.generate(edition['id'])
        value.update(status=result['status'], checks=result.get('checks'),
                     preview_url=f"http://127.0.0.1:8000/?document={did}&readingV2={edition['id']}&readingInspection=1")
    except Exception as error:
        value.update(status='failed', error=settings.sanitize(error))
        if value.get('edition'):
            f = reading.folder(value['edition'])
            value['retained_files'] = [str(p.relative_to(f)) for p in f.rglob('*') if p.is_file()]
            value['completed_chapters'] = len(list(f.glob('chapters/*/artifact.json')))
    value['seconds'] = round(time.monotonic() - started, 2)
    value['finished_at'] = reading.now()
    save(target, value)
    print(f"END {case['id']} {value['status']} {value['seconds']}s {value.get('error','')}", flush=True)
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch', required=True)
    args = parser.parse_args()
    out = store.ROOT / 'artifacts/reading-v2' / args.batch
    out.mkdir(parents=True, exist_ok=False)
    papers = json.loads((store.ROOT / 'tests/corpus/manifest.json').read_text(encoding='utf-8'))['papers']
    selected = [next(p for p in papers if p['id'] == key) for key in CASES]
    assert len(selected) == 8 and all(p['id'] not in ['attention', 'cnnic55'] for p in selected)
    before, frozen = protected(), implementation()
    save(out / 'protected-before.json', before)
    save(out / 'implementation.json', frozen)
    save(out / 'batch.json', {'started_at': reading.now(), 'cases': CASES,
         'excluded': ['attention', 'cnnic55', 'attention-page3-scan'], 'models': settings.models(),
         'version': reading.VERSION, 'document_workers': 2, 'shared_model_concurrency': settings.setting('PAPERMIND_MODEL_CONCURRENCY', '3'),
         'policy': 'first pass only; no repairs, retries of failed editions, validation promotion or publication'})
    results = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run, p, out) for p in selected]
        for future in as_completed(futures):
            results.append(future.result())
            save(out / 'generation-summary.json', {'finished': len(results), 'total': 8, 'results': results})
    after = protected()
    save(out / 'protected-after-generation.json', after)
    save(out / 'generation-summary.json', {'all_cases_finished': True, 'finished_at': reading.now(),
         'protected_unchanged': before == after, 'implementation_unchanged': frozen == implementation(),
         'results': sorted(results, key=lambda r: CASES.index(r['case']))})
    print('GENERATION BATCH FINISHED', len(results), flush=True)


if __name__ == '__main__':
    main()
