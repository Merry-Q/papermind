"""Run real public PDFs through the same product APIs; no fixture success substitutions."""
import argparse
import concurrent.futures
import json
import sys
import threading
import time
from datetime import datetime,timezone
from pathlib import Path
import httpx

ROOT=Path(__file__).resolve().parents[1]
LOCK=threading.Lock()
OUTPUT=ROOT/'data'/'benchmark-live'
OUTPUT.mkdir(parents=True,exist_ok=True)

def write_result(case_id,result):
    with LOCK:(OUTPUT/f'{case_id}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')

def check_api(r):
    if not r.is_success:raise RuntimeError(f'HTTP {r.status_code}: {r.text[:700]}')
    return r.json()

def run_case(case,base,extended=False,regenerate=False):
    started=time.monotonic();case_id=case['id'];result={'case_id':case_id,'title':case['title'],'domain':case['domain'],'page_count':case['page_count'],'sha256':case['sha256'],'source_url':case['original_url'],'started_at':datetime.now(timezone.utc).isoformat(),'status':'running','checks':{},'errors':[]}
    write_result(case_id,result)
    try:
        with httpx.Client(base_url=base,timeout=600,trust_env=False) as client:
            path=ROOT/case['file']
            with path.open('rb') as pdf:uploaded=check_api(client.post('/api/documents',files={'file':(path.name,pdf,'application/pdf')}))
            doc_id=uploaded['id'];result['document_id']=doc_id;result['product_url']=base+'/?document='+doc_id
            doc=check_api(client.get('/api/documents/'+doc_id))
            job=doc.get('job')
            if not job or job['status'] in {'failed','cancelled'} or (regenerate and job['status'] not in {'queued','running'}):
                job=check_api(client.post(f'/api/documents/{doc_id}/generation',json={}))
            result['job_id']=job['id'];write_result(case_id,result)
            previous=None;deadline=time.monotonic()+2400
            while job['status'] in {'queued','running'}:
                if time.monotonic()>deadline:raise TimeoutError('单篇生成超过40分钟，保留后台任务和当前产物')
                job=check_api(client.get('/api/jobs/'+job['id']))
                if job['stage']!=previous:
                    print(case_id,job['stage'],job.get('detail',''),flush=True);previous=job['stage']
                time.sleep(3)
            doc=check_api(client.get('/api/documents/'+doc_id))
            result.update(generation_status=doc['status'],job_status=job['status'],job_error=job.get('error'),generation_seconds=job.get('elapsed_seconds'),nodes=len(doc['nodes']),visuals=len(doc.get('visuals',[])),parser=doc.get('parser_summary'),verification=doc.get('verification'),generation_gaps=doc.get('generation_gaps',[]))
            checks=check_api(client.get(f'/api/documents/{doc_id}/checks'));result['checks']['reference_contract']=checks
            if job['status']!='completed':raise RuntimeError('生成任务失败：'+str(job.get('error')))
            result['checks']['whole_paper_ready']=doc['status']=='ready'
            result['checks']['node_ids_unique']=len({n['id'] for n in doc['nodes']})==len(doc['nodes'])
            node=doc['nodes'][-1]
            response=check_api(client.post(f'/api/documents/{doc_id}/messages',json={'node_id':node['id'],'text':'请根据这篇文档解释一项核心方法或论证的成立条件，以及一项局限。只使用原文依据。'}))
            answer=response['assistant'];result['checks']['copilot']={'provider':answer.get('provider'),'verification':answer.get('verification'),'source_count':len(answer['source_ids']),'text':answer['text'],'can_patch':answer['can_patch']}
            if answer['can_patch']:
                before=check_api(client.get(f'/api/documents/{doc_id}'))
                patch=check_api(client.post(f'/api/documents/{doc_id}/patches',json={'message_id':answer['id'],'base_revision':before['revision']}))
                applied=check_api(client.post(f'/api/documents/{doc_id}/patches/{patch["id"]}/apply',json={'base_revision':before['revision']}))
                undone=check_api(client.post(f'/api/documents/{doc_id}/patches/{patch["id"]}/undo',json={'base_revision':applied['revision']}))
                result['checks']['patch_roundtrip']=undone['revision']==before['revision']+2
            else:result['checks']['patch_roundtrip']='blocked_by_answer_verification'
            if doc.get('concepts'):
                concept=next(iter(doc['concepts'].values()))
                existing=check_api(client.get('/api/bootstrap'))['library']
                item=check_api(client.put('/api/library',json={'document_id':doc_id,'concept_id':concept['id']}))
                result['checks']['concept_save']=item['declaration']=='self_reported'
                if not any(i['id']==item['id'] for i in existing):check_api(client.delete('/api/library/'+item['id']))
            if extended:
                visual=next((v for v in doc.get('visuals',[]) if v.get('chart_or_table')),None)
                if visual:
                    visual_answer=check_api(client.post(f'/api/documents/{doc_id}/messages',json={'node_id':doc['nodes'][0]['id'],'text':'请解释这页图表表达的关系及读图限制，不要猜测模糊数值。','selected_page':visual['page']}))['assistant']
                    result['checks']['visual_question']={'verification':visual_answer.get('verification'),'observation':visual_answer.get('visual_observation'),'text':visual_answer['text']}
                else:result['checks']['visual_question']='no_chart_detected'
                external=check_api(client.post(f'/api/documents/{doc_id}/messages',json={'node_id':doc['nodes'][0]['id'],'text':'请补充一个理解本文所需而原文未展开的专业前置概念，并联网查找大学、教材或原始论文的权威定义来源。明确区分原文和外部知识。'}))['assistant']
                result['checks']['external_knowledge']={'verification':external.get('verification'),'search':external.get('external_search'),'source_ids':external['source_ids'],'text':external['text']}
            result['metrics']=check_api(client.get(f'/api/documents/{doc_id}/metrics'))
            result['status']='tested'
    except Exception as error:
        result['status']='failed';result['errors'].append(str(error))
    result['elapsed_seconds']=round(time.monotonic()-started,2);write_result(case_id,result)
    print(case_id,result['status'],result.get('generation_status'),result['errors'],flush=True)
    return result

def main():
    global OUTPUT
    p=argparse.ArgumentParser();p.add_argument('--base',default='http://127.0.0.1:8000');p.add_argument('--ids',nargs='*');p.add_argument('--extended',action='store_true');p.add_argument('--regenerate',action='store_true');p.add_argument('--include-derived',action='store_true');p.add_argument('--workers',type=int,default=2);p.add_argument('--output',type=Path,default=OUTPUT);args=p.parse_args()
    OUTPUT=args.output;OUTPUT.mkdir(parents=True,exist_ok=True)
    with httpx.Client(trust_env=False) as c:
        capabilities=check_api(c.get(args.base+'/api/capabilities'))
    if capabilities['mode']!='live':raise SystemExit('Refusing benchmark: real Qwen mode is not configured')
    manifest=json.loads((ROOT/'tests/corpus/manifest.json').read_text(encoding='utf-8'))
    cases=manifest['papers']
    if args.include_derived:
        for variant in manifest.get('derived_variants',[]):
            parent=next(p for p in manifest['papers'] if p['id']==variant['derived_from'])
            cases.append({**variant,'domain':'衍生OCR回归样本','original_url':parent['original_url']})
    if args.ids:cases=[c for c in cases if c['id'] in args.ids]
    if not cases:raise SystemExit('No matching test cases; check --ids and --include-derived')
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures=[pool.submit(run_case,case,args.base,args.extended,args.regenerate) for case in cases]
        results=[f.result() for f in concurrent.futures.as_completed(futures)]
    (OUTPUT/'summary.json').write_text(json.dumps({'generated_at':datetime.now(timezone.utc).isoformat(),'models':capabilities['models'],'results':results},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Tested:',sum(r['status']=='tested' for r in results),'Failed:',sum(r['status']=='failed' for r in results),flush=True)

if __name__=='__main__':main()
