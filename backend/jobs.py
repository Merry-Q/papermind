"""PDF preparation followed by whole-document interaction generation and publication."""
import hashlib
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from . import model_gateway as gateway, parser, settings, store
from .live_contracts import Plan, NodeBatch, Digests

POOL=None
LOCK=threading.Lock()
FUTURES={}

def now():return datetime.now(timezone.utc).isoformat()

def get_job(db,job_id):
    row=db.execute('SELECT payload FROM jobs WHERE id=?',(job_id,)).fetchone()
    return json.loads(row[0]) if row else None

def latest_job(db,doc_id):
    row=db.execute('SELECT payload FROM jobs WHERE document_id=? ORDER BY rowid DESC LIMIT 1',(doc_id,)).fetchone()
    return json.loads(row[0]) if row else None

def update_job(job_id,**changes):
    with store.connection(write=True) as db:
        job=get_job(db,job_id)
        job.update(changes);job['updated_at']=now()
        db.execute('UPDATE jobs SET payload=? WHERE id=?',(store.encode(job),job_id))
        db.execute('INSERT INTO job_events(job_id,payload) VALUES (?,?)',(job_id,store.encode({'at':now(),**changes})))
    return job

def check_cancel(job_id):
    with store.connection() as db:job=get_job(db,job_id)
    if job.get('cancel_requested'):raise InterruptedError('用户已取消，已完成部分保留')

def startup():
    global POOL
    POOL=ThreadPoolExecutor(max_workers=2,thread_name_prefix='papermind-generation')
    with store.connection() as db:
        resume=[json.loads(r[0]) for r in db.execute('SELECT payload FROM jobs') if json.loads(r[0])['status'] in {'queued','running'}]
    for job in resume:
        FUTURES[job['id']]=POOL.submit(run_job,job['id'])

def shutdown():
    if POOL:POOL.shutdown(wait=False,cancel_futures=True)

def enqueue(doc_id,force_ocr_pages=None):
    with store.connection(write=True) as db:
        doc=store.get_document(db,doc_id)
        if not doc or not doc.get('file_path'):raise ValueError('请先上传真实 PDF')
        if doc.get('supplements'):raise ValueError('重新生成前请先撤回页面补充，避免覆盖个人修改')
        active=latest_job(db,doc_id)
        if active and active['status'] in {'queued','running'}:return active
        job={'id':str(uuid4()),'document_id':doc_id,'status':'queued','stage':'queued','detail':'等待解析','created_at':now(),'updated_at':now(),'cancel_requested':False,'force_ocr_pages':force_ocr_pages or [],'error':None,'models':settings.models(),'skill_versions':{'evidence-ledger':'0.2.0','argument-plan':'0.2.0','interactive-lesson':'0.2.0'}}
        db.execute('INSERT INTO jobs VALUES (?,?,?)',(job['id'],doc_id,store.encode(job)))
        doc['status']='generating';doc['canonical_complete']=False;store.put_document(db,doc)
    if not POOL:
        startup()
        return job
    with LOCK:FUTURES[job['id']]=POOL.submit(run_job,job['id'])
    return job

def cache_value(path,work):
    if path.is_file():return json.loads(path.read_text(encoding='utf-8'))
    value=work();path.write_text(store.encode(value),encoding='utf-8');return value

def page_inputs(ir):
    by_id={s['id']:s for s in ir['sources']}
    return [{'page':p['page'],'sources':[{'id':sid,'quote':by_id[sid]['quote']} for sid in p['source_ids']]} for p in ir['pages']]

def planner_input(ir,artifacts,context,event):
    pages=page_inputs(ir)
    if len(store.encode(pages))<int(settings.setting('PAPERMIND_PLANNER_CHAR_BUDGET','320000')):return pages
    # Every page is passed through the map stage, including late results/appendices.
    result=[];batch=[];size=0;groups=[]
    for page in pages:
        length=len(store.encode(page))
        if batch and size+length>70000:groups.append(batch);batch=[];size=0
        batch.append(page);size+=length
    if batch:groups.append(batch)
    for index,group in enumerate(groups):
        event('mapping',f'长文全文归纳 {index+1}/{len(groups)}')
        mapped=cache_value(artifacts/f'map-{index}.json',lambda:gateway.structured('planner','逐页归纳核心主张、方法、数字与成立条件。每个输入页必须有一条输出，不省略后半部分。保留重要来源ID。',group,Digests,max_tokens=8000,context=context))
        expected={p['page'] for p in group}
        if {p['page'] for p in mapped['pages']} != expected:raise ValueError('长文归纳未覆盖所有输入页面')
        result.extend(mapped['pages'])
    return result

def compose_nodes(path,instruction,evidence,*,max_tokens,context):
    """Short evidence handles prevent copying long, error-prone PDF block IDs.

    Handles are losslessly expanded; unknown handles remain invalid. If a batch
    fails its strict schema twice, retry smaller nodes rather than fill missing
    fields with invented evidence or silently publish an incomplete object.
    """
    if path.is_file():return NodeBatch.model_validate(json.loads(path.read_text(encoding='utf-8'))).model_dump()
    key='sources' if 'sources' in evidence else 'original_sources'
    mapping={f'R{i:05d}':s['id'] for i,s in enumerate(evidence[key],1)}
    reverse={v:k for k,v in mapping.items()}
    def references(value,lookup):
        if isinstance(value,dict):
            return {k:[lookup.get(v,v) for v in values] if k=='source_ids' else references(values,lookup) for k,values in value.items()}
        if isinstance(value,list):return [references(v,lookup) for v in value]
        return value
    payload=references(evidence,reverse)
    payload[key]=[{**s,'id':reverse[s['id']]} for s in evidence[key]]
    try:
        value=gateway.structured('composer',instruction+' source_ids只能逐字复制提供的R编号；不得根据页码或块号推测编号。每个节点必须包含所有契约字段，formula无公式时为null。',payload,NodeBatch,skill='interactive-lesson',max_tokens=max_tokens,context=context)
        value=references(value,mapping)
    except gateway.ModelError:
        group=evidence.get('requested_nodes',[])
        if len(group)<2:raise
        value={'nodes':[]}
        for i,planned in enumerate(group):
            if context.get('job_id'):
                check_cancel(context['job_id'])
                update_job(context['job_id'],stage='composing',detail=f'批量输出未完成，拆分重试：{planned["title"]}')
            smaller={**evidence,'requested_nodes':[planned]}
            smaller[key]=[s for s in evidence[key] if s['page'] in planned['source_pages']]
            smaller['visual_observations']=[v for v in evidence.get('visual_observations',[]) if v['page'] in planned['source_pages']]
            single=compose_nodes(path.with_name(path.stem+f'-single-{i}.json'),instruction,smaller,max_tokens=min(max_tokens,8000),context=context)
            value['nodes'].extend(single['nodes'])
    value=NodeBatch.model_validate(value).model_dump()
    path.write_text(store.encode(value),encoding='utf-8')
    return value


def clean_title(title):
    title=re.sub(r'\s*[:：\-—]?\s*(?:Core Argument (?:Coverage )?Plan|核心论证覆盖图|核心论证覆盖计划|论证覆盖计划|核心论证计划|论证计划)\s*$','',title,flags=re.I).strip()
    return title or '文档讲解'

def run_job(job_id):
    started=time.monotonic()
    with store.connection() as db:
        job=get_job(db,job_id);doc=store.get_document(db,job['document_id'])
    context={'document_id':doc['id'],'job_id':job_id}
    artifacts=store.DATA/'runs'/job_id;artifacts.mkdir(parents=True,exist_ok=True)
    def event(stage,detail):
        check_cancel(job_id);update_job(job_id,status='running',stage=stage,detail=detail)
    try:
        if job.get('reading_edition_id') and doc.get('canonical_complete'):
            from . import reading_v2
            reading_v2.generate(job['reading_edition_id'],cancel_check=lambda:check_cancel(job_id))
            update_job(job_id,status='completed',stage='completed',detail='整篇交互讲解已生成并展示',result_status='ready')
            return
        event('parsing','提取全文、版面与引用锚点')
        ir=parser.parse(doc,event,force_ocr_pages=job['force_ocr_pages'])
        ir_path=artifacts/'document-ir.json';ir_path.write_text(store.encode(ir),encoding='utf-8')
        if not ir['sources']:raise ValueError('没有取得可读文字，OCR仍未解决；请检查原文件与识别配额')
        with store.connection(write=True) as db:
            current=store.get_document(db,doc['id']);current.update(sources=ir['sources'],ir_path=str(ir_path),visuals=ir['visuals'],parser_summary={k:ir[k] for k in ['parser_version','page_count','ocr_pages','two_column_pages','gaps']});store.put_document(db,current)
        event('planning','梳理全文核心论证与必需节点')
        planner_evidence=planner_input(ir,artifacts,context,event)
        plan=cache_value(artifacts/'plan.json',lambda:gateway.structured('planner',
            '阅读全文证据，建立覆盖全篇核心论证的阅读计划。title必须为原文实际标题，不加“计划/覆盖图”等内部任务措辞。通常5至10个节点，理论/哲学以论证链组织，研报以问题与证据组织。'
            '包含重要结果、假设、公式变量与局限。id用稳定英文短串；source_pages引用真实物理页。'
            'core_gaps只记录缺页、无法识别等使核心论证无法解释的证据缺口；正常研究局限不算缺口。'
            '原文未给外引方法的全部定义、原始数据、统计检验、复现细节，不属于解析缺口；不要凭常识怀疑论文数字就列缺口。',
            {'pages':planner_evidence,'visual_observations':ir['visuals'],'scope':'仅解释实际上传页；对不在上传页中的外引定义或后续章节，说明范围，不以其他版本/整篇记忆要求补全。'},Plan,skill='argument-plan',max_tokens=6000,context=context))
        plan['title']=clean_title(plan['title'])
        for n in plan['nodes']:
            if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,80}',n['id']):raise ValueError('计划节点ID不符合安全命名约定')
            if any(p<1 or p>ir['page_count'] for p in n['source_pages']):raise ValueError('计划引用了不存在的页码')
        if len({n['id'] for n in plan['nodes']})!=len(plan['nodes']):raise ValueError('计划节点ID重复')
        all_ids={s['id'] for s in ir['sources']};nodes=[];concepts={}
        with store.connection(write=True) as db:
            current=store.get_document(db,doc['id']);current.update(title=plan['title'],subtitle=plan['subtitle'],domain=plan['domain'],nodes=[],concepts={},generation_plan=plan,status='generating');store.put_document(db,current)
        for offset in range(0,len(plan['nodes']),3):
            group=plan['nodes'][offset:offset+3];wanted_pages={p for n in group for p in n['source_pages']}
            evidence=[s for s in ir['sources'] if s['page'] in wanted_pages]
            # A too-large section is explicit; never silently truncate evidence.
            if len(store.encode(evidence))>220000:raise ValueError('单组论证证据过长，需要更细的计划节点')
            event('composing',f'生成讲解 {offset+1}–{offset+len(group)}/{len(plan["nodes"])}')
            draft=compose_nodes(artifacts/f'nodes-{offset}.json',
                '为指定全部节点生成可从头到尾阅读的中文讲解，必须保持计划id，不生成额外节点。'
                'summary和paragraphs讲清机制、证据与条件；claims须覆盖正文主要事实，引用只能使用证据中真实source id。'
                'terms提供1至2个与当前论证有关的专业概念解释（不按用户等级），id英文，layer描述具体知识层。'
                '仅在能帮助理解机制或论证时选择stepper，步骤必须基于原文；其余none。不要把所有文章套进稀疏重建或算法模板。'
                'formula仅在原文可辨认且重要时提供LaTeX，否则null。原文报告的数据和结论要明确归属于作者，不包装成普遍证明。'
                '若摘要、图表与正文数字不一致，应分别引用并说明差异，不能自行择一。禁止自测、评分、编造实验或假装复现数据。',
                {'document_title':plan['title'],'domain':plan['domain'],'requested_nodes':group,'sources':evidence,'visual_observations':[v for v in ir['visuals'] if v['page'] in wanted_pages]},
                max_tokens=13000,context=context)
            if {n['id'] for n in draft['nodes']}!={n['id'] for n in group}:raise ValueError('生成节点没有完整匹配计划')
            for node in draft['nodes']:
                planned=next(n for n in group if n['id']==node['id'])
                concept_ids=[]
                for term in node.pop('terms'):
                    if set(term['source_ids'])-all_ids:continue
                    cid='concept-'+hashlib.sha256((plan['domain']+'|'+term['title']+'|'+term['layer']).encode()).hexdigest()[:16]
                    concepts[cid]={**term,'id':cid,'next':None,'domain':plan['domain'],'document_id':doc['id'],'node_id':node['id']}
                    concept_ids.append(cid)
                node.update(concepts=concept_ids,kind='steps' if node['interaction']=='stepper' else 'live_formula' if node['formula'] else 'narrative',status='readable',required=planned['required'])
                nodes.append(node)
            with store.connection(write=True) as db:
                current=store.get_document(db,doc['id']);current.update(nodes=nodes,concepts=concepts,verification={'items':[],'semantic_verification':'not_run'});store.put_document(db,current)
        check_cancel(job_id)
        with store.connection(write=True) as db:
            current=store.get_document(db,doc['id'])
            current.update(status='ready',canonical_complete=True,subtitle=plan['subtitle'],generation_gaps=ir['gaps']+[{'reason':g} for g in plan['core_gaps']],verification={'items':[],'semantic_verification':'not_run'},generated_at=now())
            current['revision']+=1;store.put_document(db,current)
        update_job(job_id,stage='interactive',detail='正在创作整篇交互讲解')
        from . import reading_v2
        edition=reading_v2.create(doc['id'])
        update_job(job_id,reading_edition_id=edition['id'])
        reading_v2.generate(edition['id'],cancel_check=lambda:check_cancel(job_id))
        update_job(job_id,status='completed',stage='completed',detail='整篇交互讲解已生成并展示',result_status='ready',elapsed_seconds=round(time.monotonic()-started,2))
    except Exception as error:
        state='cancelled' if isinstance(error,InterruptedError) else 'failed'
        with store.connection(write=True) as db:
            current=store.get_document(db,doc['id']);current['status']='ready' if current.get('canonical_complete') else 'incomplete';store.put_document(db,current)
        update_job(job_id,status=state,stage=state,detail='已完成内容保留，可检查原因后重试',error=settings.sanitize(error),elapsed_seconds=round(time.monotonic()-started,2))

def stats(doc_id):
    with store.connection() as db:
        calls=[dict(r) for r in db.execute('SELECT role,model,elapsed,usage,payload FROM model_calls') if json.loads(r['payload']).get('document_id')==doc_id]
    total=0
    for c in calls:
        usage=json.loads(c['usage']);total+=usage.get('total_tokens',usage.get('input_tokens',0)+usage.get('output_tokens',0))
    return {'calls':len(calls),'total_tokens':total,'call_seconds':round(sum(c['elapsed'] for c in calls),2),'models':sorted({c['model'] for c in calls}),'by_role':{role:sum(c['role']==role for c in calls) for role in {c['role'] for c in calls}}}
