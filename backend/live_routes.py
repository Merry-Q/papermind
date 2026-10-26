from pathlib import Path
from uuid import uuid4
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from . import copilot_runs, jobs, live_copilot, settings, store
from .contracts import ActionResult, CopilotDecision, CopilotRunRequest, GenerationRequest, KnowledgeRequest

router=APIRouter(prefix='/api')

def doc_or_404(db,doc_id):
    doc=store.get_document(db,doc_id)
    if not doc:raise HTTPException(404,'文档不存在')
    return doc

@router.get('/capabilities')
def capabilities():
    return {'mode':'live' if settings.live_enabled() else 'unconfigured','chat_context_version':3,'credential_configured':bool(settings.api_key()),'models':settings.models(),'features':{'generation':settings.live_enabled(),'ocr':settings.live_enabled(),'web_search':settings.live_enabled(),'model_fact_review':settings.live_enabled(),'pdf_region_selection':True,'copilot_runs':True},'verification_scope':'模型对照来源核验，不代表人工学术审查'}

@router.post('/documents/{doc_id}/copilot/runs',status_code=202)
def create_copilot_run(doc_id:str,body:CopilotRunRequest):
    if not body.text.strip():raise HTTPException(422,'请输入问题')
    if body.bbox and (not body.selected_page or not (0<=body.bbox[0]<body.bbox[2]<=1 and 0<=body.bbox[1]<body.bbox[3]<=1)):
        raise HTTPException(422,'框选区域必须是有效的页内归一化坐标')
    with store.connection() as db:
        doc=doc_or_404(db,doc_id)
        valid=body.node_id=='document' and not doc['is_demo'] or any(node['id']==body.node_id for node in doc['nodes'])
        if not valid:raise HTTPException(422,'提问位置不属于当前文档')
    try:return copilot_runs.create(doc,body)
    except ValueError as error:raise HTTPException(409,str(error))

@router.get('/documents/{doc_id}/copilot/runs/active')
def active_copilot_run(doc_id:str):
    with store.connection() as db:
        doc_or_404(db,doc_id)
        return copilot_runs.latest_active(db,doc_id)

@router.get('/copilot/runs/{run_id}')
def copilot_run(run_id:str):
    with store.connection() as db:value=copilot_runs.get_run(db,run_id)
    if not value:raise HTTPException(404,'Copilot 任务不存在')
    return value

@router.get('/copilot/runs/{run_id}/events')
def copilot_events(run_id:str,after:int=0):
    with store.connection() as db:
        if not copilot_runs.get_run(db,run_id):raise HTTPException(404,'Copilot 任务不存在')
        return {'events':copilot_runs.get_events(db,run_id,after)}

@router.post('/copilot/runs/{run_id}/decision')
def copilot_decision(run_id:str,body:CopilotDecision):
    try:return copilot_runs.decide(run_id,body.action,body.comment)
    except ValueError as error:raise HTTPException(409,str(error))

@router.post('/copilot/runs/{run_id}/cancel')
def cancel_copilot_run(run_id:str):
    try:return copilot_runs.cancel(run_id)
    except ValueError as error:raise HTTPException(404,str(error))

@router.post('/documents/{doc_id}/generation',status_code=202)
def generate(doc_id:str,body:GenerationRequest):
    if not settings.live_enabled():raise HTTPException(503,'请在后端配置 DASHSCOPE_API_KEY')
    with store.connection() as db:
        doc=doc_or_404(db,doc_id)
        if any(p<1 or p>doc['page_count'] for p in body.force_ocr_pages):raise HTTPException(422,'OCR页码超出文档')
    try:return jobs.enqueue(doc_id,body.force_ocr_pages)
    except ValueError as e:raise HTTPException(409,str(e))

@router.get('/jobs/{job_id}')
def job(job_id:str):
    with store.connection() as db:value=jobs.get_job(db,job_id)
    if not value:raise HTTPException(404,'任务不存在')
    return value

@router.post('/jobs/{job_id}/cancel')
def cancel(job_id:str):
    with store.connection() as db:value=jobs.get_job(db,job_id)
    if not value:raise HTTPException(404,'任务不存在')
    if value['status'] in {'completed','failed','cancelled'}:return value
    return jobs.update_job(job_id,cancel_requested=True,detail='等待当前模型调用结束后取消')

@router.get('/jobs/{job_id}/events')
def events(job_id:str,after:int=0):
    with store.connection() as db:
        if not jobs.get_job(db,job_id):raise HTTPException(404,'任务不存在')
        values=[{'event_id':r['event_id'],**json.loads(r['payload'])} for r in db.execute('SELECT event_id,payload FROM job_events WHERE job_id=? AND event_id>? ORDER BY event_id',(job_id,after))]
    return {'events':values}

@router.get('/documents/{doc_id}/metrics')
def metrics(doc_id:str):
    with store.connection() as db:doc_or_404(db,doc_id)
    return jobs.stats(doc_id)

@router.post('/documents/{doc_id}/knowledge')
def knowledge(doc_id:str,body:KnowledgeRequest):
    with store.connection() as db:
        doc=doc_or_404(db,doc_id)
        concept=doc.get('concepts',{}).get(body.concept_id)
    if not concept:raise HTTPException(404,'该概念不属于当前文档')
    try:card,sources=live_copilot.expand(doc,concept,body.question)
    except Exception as e:raise HTTPException(502,settings.sanitize(e))
    with store.connection(write=True) as db:
        current=doc_or_404(db,doc_id)
        current.setdefault('concepts',{})[card['id']]=card
        current['concepts'][body.concept_id]['next']=card['id']
        known={s['id'] for s in current['sources']}
        current['sources'].extend(s for s in sources if s['id'] not in known)
        store.put_document(db,current)
    return card

@router.post('/documents/{doc_id}/actions/{action_id}/result')
def action_result(doc_id:str,action_id:str,body:ActionResult):
    with store.connection(write=True) as db:
        doc_or_404(db,doc_id)
        rows=db.execute('SELECT id,payload FROM messages WHERE document_id=? AND role=?',(doc_id,'assistant')).fetchall()
        match=next((r for r in rows if (json.loads(r['payload']).get('action') or {}).get('id')==action_id),None)
        if not match:raise HTTPException(404,'操作不存在或不属于当前文档')
        message=json.loads(match['payload']);message['action_result']=body.model_dump()
        db.execute('UPDATE messages SET payload=? WHERE id=?',(store.encode(message),match['id']))
    return {'recorded':True}
