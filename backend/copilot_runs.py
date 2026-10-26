"""Durable, user-steerable Copilot turns with persisted progress events."""
import json
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from uuid import uuid4

from . import live_copilot, settings, store
from .contracts import ChatRequest
from .copilot import reply

POOL=None
LOCK=threading.Lock()
FUTURES={}
ACTIVE={'queued','planning','revising','awaiting_user','running','cancelling'}
TERMINAL={'completed','failed','cancelled'}
DEEP_MARKERS=('深度','研究','调研','比较','对比','评价','批判','争议','可靠性','反例','综述','多篇','跨文档','外部文献','联网')

def now():return datetime.now(timezone.utc).isoformat()

def get_run(db,run_id):
    row=db.execute('SELECT payload FROM copilot_runs WHERE id=?',(run_id,)).fetchone()
    return json.loads(row[0]) if row else None

def latest_active(db,doc_id):
    rows=db.execute('SELECT payload FROM copilot_runs WHERE document_id=? ORDER BY rowid DESC',(doc_id,)).fetchall()
    return next((value for row in rows if (value:=json.loads(row[0]))['status'] in ACTIVE),None)

def get_events(db,run_id,after=0):
    return [{'event_id':row['event_id'],**json.loads(row['payload'])} for row in db.execute(
        'SELECT event_id,payload FROM copilot_events WHERE run_id=? AND event_id>? ORDER BY event_id',(run_id,after))]

def _event(db,run_id,event_type,detail,data=None):
    payload={'type':event_type,'detail':detail,'data':data or {},'at':now()}
    db.execute('INSERT INTO copilot_events(run_id,payload) VALUES (?,?)',(run_id,store.encode(payload)))

def update(run_id,event_type=None,detail=None,**changes):
    with store.connection(write=True) as db:
        run=get_run(db,run_id)
        if not run:return None
        run.update(changes);run['updated_at']=now()
        if detail is not None:run['detail']=detail
        db.execute('UPDATE copilot_runs SET payload=? WHERE id=?',(store.encode(run),run_id))
        if event_type:_event(db,run_id,event_type,detail or '',changes)
    return run

def mode_for(text,requested):
    if requested!='auto':return requested
    compact=re.sub(r'\s+','',text)
    return 'deep' if any(marker in compact for marker in DEEP_MARKERS) or len(compact)>120 else 'quick'

def _submit(work,run_id,*args):
    global POOL
    if not POOL:
        with LOCK:
            if not POOL:POOL=ThreadPoolExecutor(max_workers=2,thread_name_prefix='papermind-copilot')
    with LOCK:FUTURES[run_id]=POOL.submit(work,run_id,*args)

def startup():
    global POOL
    with LOCK:
        if POOL:return
        POOL=ThreadPoolExecutor(max_workers=2,thread_name_prefix='papermind-copilot')
    with store.connection() as db:
        rows=[json.loads(row[0]) for row in db.execute('SELECT payload FROM copilot_runs')]
    for run in rows:
        if run['status'] in {'planning','revising'} and not run.get('cancel_requested'):
            _submit(_prepare_plan,run['id'],run.get('pending_revision_note'))
        elif run['status'] in {'queued','running','cancelling'}:
            if run.get('cancel_requested'):update(run['id'],'cancelled','已停止',status='cancelled',stage='cancelled')
            else:_submit(_execute,run['id'])

def shutdown():
    global POOL
    pool=POOL;POOL=None
    if pool:pool.shutdown(wait=False,cancel_futures=True)

def create(doc,body):
    selected_mode=mode_for(body.text,body.mode)
    run_id=str(uuid4());user_id=str(uuid4());created=now()
    request=body.model_dump();request['mode']=selected_mode
    user={'id':user_id,'role':'user','text':body.text.strip(),'node_id':body.node_id,
          'selected_text':body.selected_text,'selected_page':body.selected_page,'bbox':body.bbox,
          'run_id':run_id,'mode':selected_mode}
    run={'id':run_id,'document_id':doc['id'],'user_message_id':user_id,'assistant_message_id':None,
         'status':'queued','stage':'queued','detail':'正在准备回答' if selected_mode=='quick' else '正在准备研究计划',
         'mode':selected_mode,'requested_mode':body.mode,'request':request,'plan':None,'plan_revision':0,
         'cancel_requested':False,'error':None,'new_memory':None,'created_at':created,'updated_at':created,
         'attachment_snapshot':list(doc.get('attachments',[])),'user_message':user}
    with store.connection(write=True) as db:
        if latest_active(db,doc['id']):raise ValueError('当前文档已有进行中的 Copilot 任务，请先完成或停止它')
        db.execute('INSERT INTO copilot_runs VALUES (?,?,?)',(run_id,doc['id'],store.encode(run)))
        db.execute('INSERT INTO messages(id,document_id,role,payload) VALUES (?,?,?,?)',(user_id,doc['id'],'user',store.encode(user)))
        _event(db,run_id,'turn_created','问题已保存',{'mode':selected_mode})
    _submit(_prepare_plan if selected_mode=='deep' else _execute,run_id)
    return run

def _body(run):
    fields=ChatRequest.model_fields
    return ChatRequest.model_validate({key:value for key,value in run['request'].items() if key in fields})

def _context(run):
    with store.connection() as db:
        doc=store.get_document(db,run['document_id'])
        messages=[json.loads(row[0]) for row in db.execute(
            'SELECT payload FROM messages WHERE document_id=? AND id<>? ORDER BY rowid',(run['document_id'],run['user_message_id']))]
    if not doc:raise ValueError('文档不存在')
    doc={**doc,'attachments':list(run.get('attachment_snapshot',doc.get('attachments',[])))}
    return doc,messages

def check_cancel(run_id):
    with store.connection() as db:run=get_run(db,run_id)
    if not run or run.get('cancel_requested'):raise InterruptedError('用户已取消')

def _fixture_plan(doc,body,revision_note=None):
    comparison=any(word in body.text for word in ('比较','对比','另一篇'))
    objective=revision_note.strip() if revision_note else body.text.strip()
    return {'objective':objective,'questions':[objective],
            'use_attached_documents':comparison and bool(doc.get('attachments')),'use_external_sources':False,
            'answer_format':'comparison' if comparison else 'research_note'}

def _prepare_plan(run_id,revision_note=None):
    try:
        run=update(run_id,'plan_started','正在根据问题和当前阅读位置制定计划',status='revising' if revision_note else 'planning',stage='planning')
        check_cancel(run_id);doc,messages=_context(run);body=_body(run)
        value=_fixture_plan(doc,body,revision_note) if doc['is_demo'] or not settings.live_enabled() else live_copilot.plan(doc,body,messages,revision_note)
        check_cancel(run_id)
        if not doc.get('attachments'):value['use_attached_documents']=False
        scope_text=(revision_note or '')+' '+body.text
        if any(marker in scope_text for marker in ('不联网','不使用外部','只用原文','仅使用原文','只使用当前论文')):
            value['use_external_sources']=False
        update(run_id,'plan_ready','研究范围等待确认',status='awaiting_user',stage='awaiting_user',plan=value,
               plan_revision=run.get('plan_revision',0)+1,pending_revision_note=None)
    except InterruptedError:
        update(run_id,'cancelled','已停止，计划和问题仍保留',status='cancelled',stage='cancelled')
    except Exception as error:
        update(run_id,'failed','计划生成失败',status='failed',stage='failed',error=settings.sanitize(error))

def _progress(run_id,event_type,detail,data):
    stage={
        'document_retrieval_started':'retrieving','document_evidence_ready':'retrieving',
        'visual_read_started':'reading_visual','web_search_started':'searching',
        'source_read':'searching','answer_composition_started':'composing',
        'answer_review_started':'reviewing',
    }.get(event_type,'running')
    with store.connection() as db:run=get_run(db,run_id)
    update(run_id,event_type,detail,status='cancelling' if run and run.get('cancel_requested') else 'running',stage='cancelling' if run and run.get('cancel_requested') else stage,event_data=data)

def _persist_answer(run,doc,answer,external):
    assistant={'id':str(uuid4()),'role':'assistant','node_id':run['request']['node_id'],'run_id':run['id'],**answer}
    with store.connection(write=True) as db:
        current=store.get_document(db,run['document_id'])
        if external:
            known={source['id'] for source in current['sources']}
            current['sources'].extend(source for source in external if source['id'] not in known)
            store.put_document(db,current)
        new_memory=None
        if answer.get('memory'):
            candidate={**answer['memory'],'document_id':run['document_id'],'message_id':run['user_message_id']}
            if not db.execute('SELECT id FROM memories WHERE id=?',(candidate['id'],)).fetchone():
                new_memory={**candidate,'deleted':False}
                db.execute('INSERT INTO memories VALUES (?,?)',(new_memory['id'],store.encode(new_memory)))
        db.execute('INSERT INTO messages(id,document_id,role,payload) VALUES (?,?,?,?)',
                   (assistant['id'],run['document_id'],'assistant',store.encode(assistant)))
    return assistant,new_memory

def _execute(run_id):
    try:
        run=update(run_id,'research_started','开始读取与问题相关的证据',status='running',stage='retrieving')
        check_cancel(run_id);doc,messages=_context(run);body=_body(run)
        if doc['is_demo'] or not settings.live_enabled():
            _progress(run_id,'document_retrieval_started','正在读取教学材料',{})
            answer=reply(doc,body.text);external=[]
            _progress(run_id,'answer_review_started','教学样例使用预设来源边界',{})
        else:
            answer,external=live_copilot.answer(doc,body,messages,research_plan=run.get('plan'),
                                                on_event=lambda *args:_progress(run_id,*args),
                                                check_cancel=lambda:check_cancel(run_id))
        check_cancel(run_id)
        assistant,new_memory=_persist_answer(run,doc,answer,external)
        update(run_id,'completed','回答已经生成并完成来源核验',status='completed',stage='completed',
               assistant_message_id=assistant['id'],new_memory=new_memory,error=None)
    except InterruptedError:
        update(run_id,'cancelled','已停止；问题和已完成进度仍保留',status='cancelled',stage='cancelled')
    except Exception as error:
        update(run_id,'failed','回答生成失败；问题已保留，可以重试',status='failed',stage='failed',error=settings.sanitize(error))

def decide(run_id,action,comment=None):
    with store.connection() as db:run=get_run(db,run_id)
    if not run:raise ValueError('Copilot 任务不存在')
    if action=='cancel':return cancel(run_id)
    if run['status']!='awaiting_user':raise ValueError('当前任务不在等待计划确认状态')
    if action=='approve_plan':
        value=update(run_id,'plan_approved','研究计划已确认，等待执行',status='queued',stage='queued')
        _submit(_execute,run_id);return value
    if not comment or not comment.strip():raise ValueError('请说明希望如何修改研究计划')
    value=update(run_id,'plan_revision_requested','正在按你的要求修改计划',status='revising',stage='planning',pending_revision_note=comment.strip())
    _submit(_prepare_plan,run_id,comment.strip());return value

def cancel(run_id):
    with store.connection() as db:run=get_run(db,run_id)
    if not run:raise ValueError('Copilot 任务不存在')
    if run['status'] in TERMINAL:return run
    if run['status']=='awaiting_user':
        return update(run_id,'cancelled','计划已取消，原问题仍保留',status='cancelled',stage='cancelled',cancel_requested=True)
    return update(run_id,'cancel_requested','正在等待当前模型调用结束后停止',status='cancelling',stage='cancelling',cancel_requested=True)
