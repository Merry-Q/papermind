"""Seal only this verified preview; no default switch or corpus generation."""
import json,sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from backend import reading_v2 as r,store
eid=sys.argv[1];out=store.ROOT/'artifacts/reading-v2';f=r.folder(eid)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
for p in [out/'final-verification/report.json',out/'final-host/report.json',out/'standalone.json',out/'experience-disposition.json']:
    assert read(p)['status']=='pass',str(p)
assert read(out/'verification/fidelity-review.json')['verdict']=='pass'
assert read(out/'final-source-check.json')['status']=='pass'
with store.connection() as db:
    tables=['documents','messages','patches','library','memories']
    after={t:hashlib.sha256(json.dumps([tuple(row) for row in db.execute('SELECT * FROM '+t+' ORDER BY rowid')],ensure_ascii=False).encode()).hexdigest() for t in tables}
before=read(out/'protected-before.json');assert before==after,'业务数据发生变化'
(out/'protected-after.json').write_text(store.encode(after),encoding='utf-8')
item=r.mark_validated(eid,{k:'pass' for k in ['structure','browser','calculations','fidelity','experience','host']})
artifact=read(f/'artifact.json');data=read(f/'data.json')
target=out/'attention-is-all-you-need-v2.html';target.write_text(r.frame_html(artifact,data,item,'standalone-export'),encoding='utf-8')
manifest={'edition':eid,'document':item['document_id'],'status':'validated-preview','default_changed':False,'other_papers_tested':False,'protected_data_unchanged':True,'artifact_hash':item['artifact_hash'],'data_hash':item['data_hash'],'runtime_hash':item['runtime_hash'],'url':f'http://127.0.0.1:8000/?document={item["document_id"]}&readingV2={eid}','export':str(target),'source_review':'verification/fidelity-review.json + final-source-check.json','experience_review':'experience-disposition.json','page_checks':16,'host_checks':8,'backend_tests':54}
(out/'preview-manifest.json').write_text(store.encode(manifest),encoding='utf-8');print(store.encode(manifest))
