"""Resume other real materials without changing published or first-pass editions."""
import json
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend import store, reading_v2 as r, jobs, settings, presentation_jobs
from benchmark_reading_v2 import protected, save

OUT = store.ROOT / 'artifacts/reading-v2/other-materials'
CASES = [
 ('rag','pdf-23e3249e9a1e7541','ff61987b-4552-40e5-ab3d-2015e77d6774'),
 ('adaptive-dcs-somp','pdf-b4deafe808239771','92c47ac1-5693-439a-9140-944c5c0b2ce0'),
 ('shannon','pdf-6e4e3411984f3edf','284336eb-c194-44fe-a682-3cc691048b9d'),
 ('lyrics','pdf-66fe209b72eb93c6','3ea2996d-d812-488e-ae72-6f73eb7a6e61'),
 ('moral-machine','pdf-59c4f6158add045b',None),
 ('simulation-argument','pdf-be823e12764a35cd',None),
 ('generative-ai-work','pdf-ac0a4e183aa6f936',None),
 ('macroeconomics-ai','pdf-b0183405d850db11',None),
 ('hyperbolic-location','pdf-473e344b1814e453',None),
 ('transformer-excerpt','pdf-1a02a680ff1cd6e0',None),
 ('5g-overview','pdf-fe9119a9c453151a',None),
]


def canonical(did, dest):
    with store.connection() as db:
        doc=store.get_document(db,did)
    if doc['status']=='ready':return
    # New run, with the exact prior document retained for audit/rollback.
    save(dest/'canonical-before.json',doc)
    jid=str(uuid4())
    job={'id':jid,'document_id':did,'status':'queued','stage':'queued','detail':'新版呈现前补齐原文讲解',
         'created_at':r.now(),'updated_at':r.now(),'cancel_requested':False,'force_ocr_pages':[],
         'error':None,'models':settings.models()}
    with store.connection(write=True) as db:
        db.execute('INSERT INTO jobs VALUES (?,?,?)',(jid,did,store.encode(job)))
    save(dest/'canonical-run.json',{'job':jid,'document':did})
    jobs.run_job(jid)
    with store.connection() as db:doc=store.get_document(db,did)
    save(dest/'canonical-after.json',doc)
    if doc['status']!='ready':
        raise ValueError('原始讲解仍有核验缺口；保留记录，不能绕过发布门禁')


def run(case):
    key,did,parent=case
    dest=OUT/key;dest.mkdir(exist_ok=True)
    record=dest/'generation.json'
    value=json.loads(record.read_text(encoding='utf-8')) if record.exists() else {
        'case':key,'document_id':did,'parent':parent,'started_at':r.now()}
    start=time.monotonic()
    try:
        canonical(did,dest)
        if not value.get('edition'):
            item=r.create(did);value['edition']=item['id']
            if parent:
                shutil.copytree(r.folder(parent),r.folder(item['id']),dirs_exist_ok=True)
            save(record,value)
        eid=value['edition']
        value.update(folder=str(r.folder(eid)),status='running')
        save(record,value)
        print('START',key,eid,flush=True)
        item=r.generate(eid)
        value.update(status=item['status'],checks=item['checks'],error=None,
          preview_url=f'http://127.0.0.1:8000/?document={did}&readingV2={eid}&readingInspection=1')
    except Exception as e:
        value.update(status='failed',error=settings.sanitize(e))
    value.update(seconds=round(time.monotonic()-start,2),finished_at=r.now())
    save(record,value)
    print('END',key,value['status'],value.get('error',''),flush=True)
    return value


if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    if not (OUT/'protected-before.json').exists():
        save(OUT/'protected-before.json',protected())
        with store.connection() as db:
            save(OUT/'defaults-before.json',[dict(row) for row in db.execute('SELECT * FROM reading_defaults')])
        save(OUT/'batch.json',{'started_at':r.now(),'cases':[c[0] for c in CASES],
             'excluded':['cnnic55','synthetic demos'],'models':settings.models(),
             'policy':'clone cached editions; finish first-pass checks before repairs; publish only after evidence-backed validation'})
    # This batch makes V2 editions explicitly; do not trigger an unrelated V1 generation.
    presentation_jobs.enqueue_after_document=lambda *_:None
    results=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(run,c) for c in CASES]):
            results.append(future.result())
            save(OUT/'generation-summary.json',{'finished':len(results),'total':len(CASES),'results':results})
    save(OUT/'generation-summary.json',{'all_cases_finished':True,'finished_at':r.now(),'results':results})
    save(OUT/'protected-after-generation.json',protected())
    print('ALL GENERATION FINISHED',flush=True)
