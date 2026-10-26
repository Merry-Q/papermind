"""Targeted real-model edge retests; preserves first-pass evidence.

Invokes the exact backend service functions against persisted real documents.
Generation benchmarks and browser tests separately exercise HTTP routes.
"""
import json
import time
from pathlib import Path
from datetime import datetime,timezone
from backend import store,live_copilot
from backend.contracts import ChatRequest

OUT=store.ROOT/'data'/'benchmark-after-fixes'/'edge-retests.json'
OUT.parent.mkdir(parents=True,exist_ok=True)

def document(did):
    with store.connection() as db:return store.get_document(db,did)

def main():
    report={'started_at':datetime.now(timezone.utc).isoformat(),'mode':'actual_qwen_backend_functions','tests':[]}
    def run(name,fn):
        started=time.monotonic()
        try:r={'name':name,'status':'tested','result':fn()}
        except Exception as error:r={'name':name,'status':'failed','error':str(error)}
        r['seconds']=round(time.monotonic()-started,2);report['tests'].append(r)
        OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(name,r['status'],r.get('error',''),flush=True)
    def visual():
        doc=document('pdf-b4deafe808239771')
        body=ChatRequest(node_id=doc['nodes'][0]['id'],selected_page=3,text='请解释这一页表格和场景图分别表达的关系，严格区分原图观察和无法确定的部分，不要猜测模糊数值。')
        value,_=live_copilot.answer(doc,body,[]);return value
    run('visual_answer_review_sees_actual_image',visual)
    def external():
        doc=document('pdf-66fe209b72eb93c6')
        term=next(v for v in doc['concepts'].values() if '分布式表示' in v['title'])
        card,sources=live_copilot.expand(doc,term,'Explain the negative sampling training objective in word2vec, including why noise examples are introduced. The uploaded lyrics paper does not derive it. Support the definition and equation with an original research paper, and clearly distinguish it from the lyrics paper.')
        external_ids={s['id'] for s in sources}
        return {'card':card,'fetched_external_sources':sources,'cites_external':bool(set(card['source_ids'])&external_ids)}
    run('knowledge_beyond_uploaded_paper_with_external_evidence',external)
    def philosophy():
        doc=document('pdf-be823e12764a35cd')
        value,_=live_copilot.answer(doc,ChatRequest(node_id=doc['nodes'][-1]['id'],text='请仅根据上传原文说明三分论证的逻辑强度：三个命题是否必须互斥？不要把至少一个为真加强为只有一个为真。给出原句支持。'),[])
        return value
    run('philosophy_no_unwarranted_exclusivity',philosophy)
    report['finished_at']=datetime.now(timezone.utc).isoformat();OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':main()
