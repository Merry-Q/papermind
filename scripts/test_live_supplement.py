"""Finish boundary tests without regenerating or repairing the primary benchmark."""
import concurrent.futures
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
import httpx

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'benchmark-live'/'supplement-before-fixes.json'
BASE='http://127.0.0.1:8000'

def call(client,method,url,**kwargs):
    r=client.request(method,'/api'+url,**kwargs)
    if not r.is_success:raise RuntimeError(f'{method} {url}: {r.status_code} {r.text[:600]}')
    return r.json()

def case_result(name,work):
    started=time.monotonic()
    try:
        with httpx.Client(base_url=BASE,trust_env=False,timeout=600) as c:
            value=work(c)
        return {'name':name,'status':'tested','result':value,'seconds':round(time.monotonic()-started,2)}
    except Exception as e:
        return {'name':name,'status':'failed','error':str(e),'seconds':round(time.monotonic()-started,2)}

def finish_case(name):
    record=json.loads((ROOT/'data'/'benchmark-live'/f'{name}.json').read_text(encoding='utf-8'))
    def work(c):
        doc=call(c,'GET','/documents/'+record['document_id']);did=doc['id'];values={}
        if doc.get('concepts'):
            concept=next(iter(doc['concepts'].values()))
            before=call(c,'GET','/bootstrap')['library']
            item=call(c,'PUT','/library',json={'document_id':did,'concept_id':concept['id']})
            if not any(i['id']==item['id'] for i in before):
                values['library_delete']=call(c,'DELETE','/library/'+quote(item['id'],safe=''))
            else:values['library_delete']='preexisting_item_preserved'
        for label,question in [('external_knowledge','请联网补充理解本文所需而原文未展开的一个概念，必须用大学、教材或原始论文正文支持。明确区分原文与外部知识。')]:
            if not doc['nodes']:values[label]='blocked_no_generated_nodes';continue
            values[label]=call(c,'POST',f'/documents/{did}/messages',json={'node_id':doc['nodes'][0]['id'],'text':question})['assistant']
        values['generation_status_unchanged']=call(c,'GET','/documents/'+did)['status']==doc['status']
        return values
    return work

def recursive(c):
    doc=call(c,'GET','/documents/pdf-bdfaa68d8984f0dc')
    parent=next((v for v in doc['concepts'].values() if '位置编码' in v['title']),next(iter(doc['concepts'].values())))
    cards=[]
    for question in ['Explain the mathematical definition and role of positional encoding in the Transformer. Use the original Attention Is All You Need paper as evidence.', 'Explain why sinusoidal positional encoding uses multiple frequencies and how this relates to relative positions. Distinguish author statements from teaching intuition.']:
        card=call(c,'POST',f'/documents/{doc["id"]}/knowledge',json={'concept_id':parent['id'],'question':question})
        cards.append(card);parent=card
    return {'cards':cards,'linked_chain':call(c,'GET','/documents/'+doc['id'])['concepts'][cards[0]['id']].get('next')==cards[1]['id']}

def attached(c):
    did='pdf-23e3249e9a1e7541';other='pdf-bdfaa68d8984f0dc'
    doc=call(c,'GET','/documents/'+did)
    attachment=call(c,'POST',f'/documents/{did}/attachments',json={'document_id':other})
    reply=call(c,'POST',f'/documents/{did}/messages',json={'node_id':doc['nodes'][0]['id'],'text':'请比较当前RAG论文与附加的Attention Is All You Need中非参数化检索记忆和注意力机制的作用。只用这两份原文，分别指出依据，不能把二者混为同一方法。'})['assistant']
    return {'attachments':attachment,'answer':reply,'cites_both':any(s.startswith(did+'-') for s in reply['source_ids']) and any(s.startswith(other+'-') for s in reply['source_ids'])}

def main():
    result={'started_at':datetime.now(timezone.utc).isoformat(),'phase':'before_fixes','note':'Server had stopped between turns; restarted unchanged on-disk source. capability v2 was already pending before user instruction. No new fixes made.','results':[]}
    with httpx.Client(base_url=BASE,trust_env=False) as c:result['capabilities']=call(c,'GET','/capabilities')
    tasks=[('recursive_knowledge_two_layers',recursive),('real_attached_comparison',attached),('finish_philosophy',finish_case('simulation-argument')),('finish_scan',finish_case('attention-page3-scan')),('partial_cn_report',finish_case('cnnic55'))]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        pending=[pool.submit(case_result,n,w) for n,w in tasks]
        for f in concurrent.futures.as_completed(pending):
            r=f.result();result['results'].append(r);OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(r['name'],r['status'],r.get('error',''),flush=True)
    result['finished_at']=datetime.now(timezone.utc).isoformat();OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':main()
