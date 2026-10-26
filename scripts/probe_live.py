"""Explicit live capability check; never prints or saves the API credential."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend import model_gateway as gateway, parser, retrieval, settings, store

store.initialize()
results={'models':settings.models(),'credential_configured':bool(settings.api_key()),'checks':{}}
def check(name,work):
    try:results['checks'][name]={'ok':True,'result':work()}
    except Exception as error:results['checks'][name]={'ok':False,'error':settings.sanitize(error)}
    (store.DATA/'live-probe.json').write_text(store.encode(results),encoding='utf-8')
    print(name,json.dumps(results['checks'][name],ensure_ascii=True)[:1500],flush=True)

check('planner_json',lambda:gateway.request('planner',[{'role':'user','content':'只输出JSON：{"connected":true}'}],max_tokens=30))
sample=store.ROOT/'data'/'test-corpus'/'attention-page3-scan.pdf'
if not sample.exists():
    candidates=list((store.ROOT/'data'/'test-corpus').glob('*scan*.pdf'))
    if candidates:sample=candidates[0]
if sample.exists():
    check('dedicated_ocr',lambda:{'text_excerpt':gateway.ocr(parser.page_image(sample,1))[:900]})
check('web_search_and_fetch',lambda:retrieval.web_search('Attention Is All You Need scaled dot product attention original paper',max_sources=2))
print('Saved:',store.DATA/'live-probe.json',flush=True)
