"""Whole-document interactive readings: successful generation publishes immediately."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
from html.parser import HTMLParser
import json
import re
import secrets
import threading
from datetime import datetime, timezone
from uuid import uuid4
import pymupdf
from . import store, model_gateway as gateway, parser, settings
from .reading_v2_contracts import ReadingPlan, PageEvidence, ReadingArtifact

VERSION='reading.v2.2'
POOL=None
LOCK=threading.RLock()

def now(): return datetime.now(timezone.utc).isoformat()
def digest(value): return hashlib.sha256(store.encode(value).encode()).hexdigest()
def document_hash(doc):
    return digest({'nodes':doc['nodes'],'sources':doc['sources'],'file':doc.get('file_path')})

def initialize():
    with store.connection(write=True) as db:
        db.execute('CREATE TABLE IF NOT EXISTS reading_editions(id TEXT PRIMARY KEY,document_id TEXT NOT NULL,payload TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS reading_defaults(document_id TEXT PRIMARY KEY,edition_id TEXT NOT NULL)')

def get(eid):
    initialize()
    with store.connection() as db: row=db.execute('SELECT payload FROM reading_editions WHERE id=?',(eid,)).fetchone()
    return json.loads(row[0]) if row else None

def put(value):
    initialize();value={**value,'updated_at':now()}
    with store.connection(write=True) as db:
        db.execute('INSERT INTO reading_editions VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload',(value['id'],value['document_id'],store.encode(value)))
    return value

def update(eid,**changes): return put({**get(eid),**changes})
def folder(eid):
    if not re.fullmatch(r'[a-f0-9-]{36}',eid): raise ValueError('无效呈现版本')
    return store.DATA/'reading-v2'/eid

def cached(path,fn):
    if path.exists(): return json.loads(path.read_text(encoding='utf-8'))
    value=fn();path.write_text(store.encode(value),encoding='utf-8');return value

def create(did):
    with store.connection() as db: doc=store.get_document(db,did)
    if not doc or doc.get('is_demo') or doc['status']!='ready': raise ValueError('需要已生成正文的真实文档')
    value={'id':str(uuid4()),'document_id':did,'version':VERSION,'status':'queued','stage':'queued','created_at':now(),'base_hash':document_hash(doc),'error':None}
    put(value);folder(value['id']).mkdir(parents=True);return value

def latest(did):
    initialize()
    with store.connection() as db:
        row=db.execute('SELECT payload FROM reading_editions WHERE document_id=? ORDER BY rowid DESC LIMIT 1',(did,)).fetchone()
    return json.loads(row[0]) if row else None


def startup():
    global POOL
    initialize()
    POOL=ThreadPoolExecutor(max_workers=1,thread_name_prefix='reading-v2')
    # Previously generated drafts no longer need a separate release approval.
    with store.connection() as db:
        editions=[json.loads(row[0]) for row in db.execute('SELECT payload FROM reading_editions ORDER BY rowid')]
        owned={job.get('reading_edition_id') for row in db.execute('SELECT payload FROM jobs') if (job:=json.loads(row[0]))['status'] in {'queued','running'}}
    for item in editions:
        if item['status'] in {'draft','validated'}:
            try:publish(item['id'])
            except (ValueError,OSError,KeyError,json.JSONDecodeError):continue
    if settings.live_enabled():
        for item in editions:
            if item['status'] in {'queued','running'} and item['id'] not in owned:POOL.submit(generate,item['id'])


def shutdown():
    global POOL
    if POOL:POOL.shutdown(wait=False,cancel_futures=True)
    POOL=None


def enqueue(did):
    global POOL
    with LOCK:
        active=latest(did)
        if active and active['status'] in {'queued','running'}:return active
        value=create(did)
        if POOL is None:POOL=ThreadPoolExecutor(max_workers=1,thread_name_prefix='reading-v2')
        POOL.submit(generate,value['id'])
        return value


def cancel(eid,did):
    with LOCK:
        item=get(eid)
        if not item or item['document_id']!=did:raise ValueError('生成任务不存在')
        if item['status'] not in {'queued','running'}:return item
        return update(eid,cancel_requested=True)


def check_cancel(eid):
    if get(eid).get('cancel_requested'):raise InterruptedError('生成已取消，已完成内容保留')

def evidence(doc):
    sources={f'S{i:03d}':s for i,s in enumerate(doc['sources'],1)}
    with pymupdf.open(doc['file_path']) as pdf:
        pages=[{'page':i+1,'text':p.get_text(sort=True)} for i,p in enumerate(pdf)]
    # Full source evidence is retained; the planner sees the whole document.
    return {'title':doc['title'],'nodes':doc['nodes'],'pages':pages,
            'sources':{k:{'id':s['id'],'page':s['page'],'quote':s['quote']} for k,s in sources.items()},
            'concepts':doc.get('concepts',{})}

def normalize_plan(plan,pack):
    # An exact canonical source ID and its short alias identify the same evidence.
    reverse={s['id']:key for key,s in pack['sources'].items()}
    value=json.loads(store.encode(plan))
    for chapter in value['chapters']:
        chapter['sources']=[reverse.get(s,s) for s in chapter['sources']]
    return value

def generate(eid,acceptance_interface=None,*,cancel_check=None):
    item=get(eid);did=item['document_id'];f=folder(eid);f.mkdir(parents=True,exist_ok=True)
    context={'document_id':did,'reading_edition_id':eid,'feature':VERSION}
    def checkpoint():
        check_cancel(eid)
        if cancel_check:cancel_check()
    try:
        checkpoint()
        with store.connection() as db: doc=store.get_document(db,did)
        if document_hash(doc)!=item['base_hash']:raise ValueError('原文内容已经改变')
        pack=cached(f/'evidence.json',lambda:evidence(doc))
        update(eid,status='running',stage='planning',error=None)
        plan=normalize_plan(cached(f/'plan.json',lambda:gateway.structured('planner','规划这篇完整论文的交互阅读作品。覆盖每个原节点，依据原文组织，不照抄章节目录。选择少量必要原图页，为交互给出可观察结果和独立验收点。',pack,ReadingPlan,skill='reading-v2-plan',max_tokens=8500,thinking=True,context=context)),pack)
        checkpoint()
        update(eid,stage='evidence',plan=plan)
        def read_page(page):
            prompt=('为整篇互动讲解读取此原页。只转录可辨认的真实表格和图注，不解释性填数。输出JSON Schema：'+store.encode(PageEvidence.model_json_schema())+
                    '。page='+str(page)+'。保留表头、实验集、单位、正文与表格的数值差异。表格values键必须使用columns中的原始列名，值保留原始字面量。未列出的base继承值仅可在notes说明，不能推测表格缺项。每个表给稳定id，每行给稳定id。所有可辨认数据行都要读取，不能只挑模型最好的一行。')
            return PageEvidence.model_validate(gateway.request('vision',gateway.image_message(parser.page_image(doc['file_path'],page),prompt),max_tokens=12000,context=context)).model_dump()
        # Do not let a planner's image quota hide the tables used by its arguments.
        table_pages={p['page'] for p in pack['pages'] if re.search(r'(?m)^\s*Table\s+\d+\s*:',p['text'])}
        visual_pages=sorted(set(plan['visual_pages'])|table_pages)
        (f/'visual-dependencies.json').write_text(store.encode(visual_pages),encoding='utf-8')
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures={p:pool.submit(cached,f/f'page-{p}.json',lambda p=p:read_page(p)) for p in visual_pages}
            visuals=[future.result() for future in futures.values()]
        tables=[]
        for page in visuals:
            for table in page['tables']:tables.append({**table,'id':f'p{page["page"]}-{table["id"]}','page':page['page']})
        data={'tables':tables,'sources':pack['sources'],'nodes':[{'id':n['id'],'title':n['title'],'concepts':n.get('concepts',[])} for n in doc['nodes']],'concepts':doc.get('concepts',{})}
        (f/'data.json').write_text(store.encode(data),encoding='utf-8')
        checkpoint()
        update(eid,stage='authoring')
        payload={'plan':plan,'evidence':pack,'visual_evidence':visuals,'runtime_data':data,'acceptance_interface':acceptance_interface}
        (f/'author-input.json').write_text(store.encode(payload),encoding='utf-8')
        from .reading_v2_author import compose
        artifact=compose(f,plan,pack,data,acceptance_interface,context,cached,checkpoint)
        (f/'artifact.json').write_text(store.encode(artifact),encoding='utf-8')
        enforce_execution_boundary(artifact)
        (f/'candidate.html').write_text(frame_html(artifact,data,item,'standalone-export'),encoding='utf-8')
        checkpoint()
        publish(eid)
        return get(eid)
    except Exception as error:
        state='cancelled' if isinstance(error,InterruptedError) else 'failed'
        update(eid,status=state,stage=state,error=settings.sanitize(error));raise

ALLOWED=set('article main header footer nav aside section div p span strong em small code pre h1 h2 h3 h4 h5 ul ol li button details summary table thead tbody tr th td caption figure figcaption svg g rect circle ellipse line polyline polygon path text tspan defs marker pattern lineargradient radialgradient stop title desc br hr input select option label output canvas math mi mo mn mrow mfrac msqrt msup msub fieldset legend sup sub a dl dt dd'.split())
VOID={'input','br','hr'}

def external_url(value):
    return any(not url.strip().strip('\"\'').startswith('#') for url in re.findall(r'url\(\s*([^)]*?)\s*\)',value,re.I))

class MarkupCheck(HTMLParser):
    def __init__(self,data):
        super().__init__(convert_charrefs=True);self.ids=set();self.refs=set();self.errors=[];self.data=data
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag not in ALLOWED:self.errors.append('不允许的标签：'+tag)
        for name,value in attrs.items():
            if name.startswith('on') or name in {'src','srcdoc','action','formaction','form','autofocus'}: self.errors.append('不允许的属性：'+name)
            if name in {'href','xlink:href'} and not (value or '').startswith('#'): self.errors.append('只允许页内锚点')
            if value and external_url(value):self.errors.append('属性不允许外部资源')
            if name=='id':
                if value in self.ids:self.errors.append('重复ID：'+value)
                if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*',value or '') or value=='pm-local-source':self.errors.append('无效ID：'+str(value))
                self.ids.add(value)
            if name=='data-source': self.refs.add(value)
        if tag=='input' and attrs.get('type','text') not in {'range','number','checkbox','radio','text'}: self.errors.append('不允许的输入类型')
    handle_startendtag=handle_starttag

def enforce_execution_boundary(artifact):
    ReadingArtifact.model_validate(artifact)
    check=MarkupCheck({});check.feed(artifact['html'])
    if re.search(r'@import',artifact['css'],re.I) or external_url(artifact['css']):check.errors.append('CSS不允许外部资源')
    if re.search(r'</(?:script|style)',artifact['javascript']+artifact['css'],re.I):check.errors.append('产物终止标签不允许')
    forbidden=r'\b(?:fetch|XMLHttpRequest|WebSocket|EventSource|localStorage|sessionStorage|indexedDB|eval|Worker|SharedWorker)\s*(?:\(|\.)|\bnew\s+Function\b|\bimport\s*(?:\(|\s)|\b(?:window|globalThis|self)\s*\.\s*(?:parent|top|opener|location)|\b(?:parent|top|opener)\s*\.\s*postMessage|\bdocument\s*\.\s*(?:cookie|write)|\blocation\s*\.'
    if re.search(forbidden,artifact['javascript']):check.errors.append('脚本包含外部访问或动态执行')
    errors=[e for e in check.errors if not e.startswith(('重复ID：','无效ID：'))]
    if errors:raise ValueError('；'.join(errors))


def safe_json(value):return store.encode(value).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')

def frame_html(artifact,data,item,channel,standalone=False):
    from .reading_math import render_math
    nonce=secrets.token_urlsafe(24)
    csp=f"default-src 'none'; script-src 'nonce-{nonce}'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'; frame-src 'none'; object-src 'none'; worker-src 'none'; base-uri 'none'; form-action 'none'"
    config={'edition':item['id'],'document':item['document_id'],'channel':channel,'data':data,'standalone':standalone}
    kernel=(store.ROOT/'frontend'/'reading-v2-runtime.js').read_text(encoding='utf-8')
    return ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta http-equiv="Content-Security-Policy" content="'+csp+'"><title>'+__import__('html').escape(artifact['title'])+'</title><style>'
            '*,*::before,*::after{box-sizing:border-box}html{scroll-behavior:auto}body{margin:0;min-width:0}button,input,select{font:inherit}button{cursor:pointer}canvas,svg{max-width:100%}button:focus-visible,input:focus-visible,select:focus-visible,a:focus-visible{outline:2px solid #315cc8;outline-offset:4px}'
            '#pm-local-source{position:fixed;inset:auto 12px 12px;background:#fff;color:#26364b;border:1px solid #61748c;padding:22px;z-index:99999;max-height:65vh;overflow:auto;font:15px/1.8 system-ui}#pm-local-source button{padding:8px 12px;margin-top:12px}#pm-local-source blockquote{white-space:pre-wrap;margin:12px 0}'
            '.pm-user-note{margin:24px 0;padding:20px;background:#edf2ff;color:#26364b;font:15px/1.9 system-ui}.pm-user-note h4{margin:0 0 10px}.pm-user-note p{white-space:pre-wrap}.pm-user-note button{margin:5px;padding:6px 10px}'
            '.pm-reading-tools{display:flex;flex-wrap:wrap;gap:8px 18px;margin-top:24px;padding-top:14px;border-top:1px solid #d6dcd9}.pm-reading-tools button{border:0;background:transparent;color:#265976;text-decoration:underline;text-underline-offset:4px;font-size:13px;padding:6px 0}'
            '@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}}'
            +artifact['css']+'</style></head><body>'+render_math(artifact['html'])+
            '<script nonce="'+nonce+'">const PM_CONFIG='+safe_json(config)+';'+kernel+'</script>'+
            '<script nonce="'+nonce+'">try{'+artifact['javascript']+';const pmDone=()=>{if(document.body.dataset.pmError)return;document.body.dataset.pmInitialized="true";window.dispatchEvent(new Event("pm-initialized"));};if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",pmDone,{once:true});else pmDone();}catch(error){document.body.dataset.pmError=error.message;window.dispatchEvent(new ErrorEvent("error",{message:error.message}));}</script></body></html>')

def load_completed(eid,did=None):
    item=get(eid)
    if not item or (did and item['document_id']!=did):raise ValueError('呈现版本不存在或不属于本文')
    if item['status'] not in {'completed','validated'}:raise ValueError('交互讲解尚未生成完成')
    f=folder(eid)
    artifact=ReadingArtifact.model_validate(json.loads((f/'artifact.json').read_text(encoding='utf-8'))).model_dump()
    data=json.loads((f/'data.json').read_text(encoding='utf-8'))
    return item,artifact,data


def publish(eid):
    # Atomic completion + default pointer; no browser/model/quality acceptance gate.
    with LOCK:
        item=get(eid)
        f=folder(eid)
        artifact=ReadingArtifact.model_validate(json.loads((f/'artifact.json').read_text(encoding='utf-8'))).model_dump()
        data=json.loads((f/'data.json').read_text(encoding='utf-8'))
        with store.connection(write=True) as db:
            doc=store.get_document(db,item['document_id'])
            if not doc or document_hash(doc)!=item['base_hash']:raise ValueError('生成期间正文已改变，请重新生成')
            if item.get('cancel_requested'):raise InterruptedError('生成已取消')
            if item['status'] not in {'running','draft','validated','completed'}:raise ValueError('此版本尚未生成完成')
            latest_row=db.execute('SELECT id FROM reading_editions WHERE document_id=? ORDER BY rowid DESC LIMIT 1',(item['document_id'],)).fetchone()
            if item['status']=='running' and latest_row[0]!=eid:raise ValueError('已有较新的生成任务')
            item.update(status='completed',stage='completed',error=None,updated_at=now(),artifact_hash=digest(artifact),data_hash=digest(data))
            db.execute('UPDATE reading_editions SET payload=? WHERE id=?',(store.encode(item),eid))
            db.execute('INSERT INTO reading_defaults(document_id,edition_id) VALUES (?,?) ON CONFLICT(document_id) DO UPDATE SET edition_id=excluded.edition_id',(item['document_id'],eid))
        return {'id':eid,'document_id':item['document_id'],'status':'published'}


def default_edition(did):
    initialize()
    with store.connection() as db:
        row=db.execute('SELECT edition_id FROM reading_defaults WHERE document_id=?',(did,)).fetchone()
    if not row:return None
    try:
        item,artifact,_=load_completed(row[0],did)
        return {'id':item['id'],'document_id':did,'status':'published','title':artifact['title']}
    except (ValueError,OSError,KeyError,json.JSONDecodeError):return None


def default_document():
    initialize()
    with store.connection() as db:
        ids=[row[0] for row in db.execute('SELECT document_id FROM reading_defaults ORDER BY rowid DESC')]
    return next((did for did in ids if default_edition(did)),None)
