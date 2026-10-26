"""Source-scoped real dialogue, visual selections, external evidence and recursive knowledge."""
import hashlib
import json
import re
from uuid import uuid4
from . import model_gateway as gateway, parser, retrieval, store
from .live_contracts import Answer, AnswerReview, CopilotResearchPlan, Knowledge, SearchQuery

def scope(doc):
    sources=list(doc.get('sources',[]));attached=[]
    with store.connection() as db:
        for doc_id in doc.get('attachments',[]):
            other=store.get_document(db,doc_id)
            if other:
                attached.append({'id':other['id'],'title':other['title']})
                sources.extend(other['sources'])
        memories=[m for m in store.items(db,'memories') if not m.get('deleted')]
    return sources,attached,memories

def review_answer(text,sources,context,visual_image=None):
    if visual_image is not None:
        prompt=('对照实际提供的原页/框选图像与文本来源，独立核验回答。图像本身是视觉主张的证据，不能仅因文字抽取没包含图例就判不支持。'
                '同时不得以先前视觉模型描述代替原图；看不清的数字或推断标记不足。输出JSON，verdict=supported/insufficient/contradicted，issues为字符串数组。'
                '\n回答：'+text+'\n文本来源：'+store.encode(sources))
        return AnswerReview.model_validate(gateway.request('vision',gateway.image_message(visual_image,prompt),max_tokens=2500,context=context)).model_dump()
    return gateway.structured('reviewer','核验回答中关于原文的事实，以及外部定义/公式，是否在所给来源的适用条件下得到支持。'
                              '承认证据不足的句子和清楚标记的教学类比可以保留；不能因为有引用就判定支持。'
                              '重点检查数字、图表、条件、作者主张与外部知识是否混淆。',
                              {'answer':text,'sources':sources},AnswerReview,max_tokens=2000,context=context)

def plan(doc,body,messages,revision_note=None):
    current=next((n for n in doc['nodes'] if n['id']==body.node_id),None)
    if current is None and body.node_id=='document':
        current={'id':'document','title':doc['title'],'summary':doc.get('subtitle','')}
    if current is None:raise ValueError('提问位置不属于当前文档')
    attached=[]
    with store.connection() as db:
        for doc_id in doc.get('attachments',[]):
            other=store.get_document(db,doc_id)
            if other:attached.append({'id':other['id'],'title':other['title']})
    instruction=('为一次论文阅读中的深度问答制定短计划。计划必须直接服务于用户问题，不做理解测试。'
                 'questions给1至4个可执行子问题；只有确实需要原文之外的权威材料时才启用外部来源。'
                 '附加文献只能使用列表中用户已经附加的文献。不要建议扩大到其他本地文档。')
    if revision_note:instruction+=' 用户正在修改上一版计划，必须落实其补充或缩小范围的要求。'
    return gateway.structured('copilot',instruction,{
        'document':{'id':doc['id'],'title':doc['title']},'current_node':current,
        'question':body.text,'selected_text':body.selected_text or '',
        'attached_documents':attached,'revision_note':revision_note,
        'recent_messages':[{'role':m['role'],'text':m['text']} for m in messages[-8:]],
    },CopilotResearchPlan,max_tokens=1800,context={'document_id':doc['id'],'task':'copilot_plan'})

def _notify(callback,event_type,detail,**data):
    if callback:callback(event_type,detail,data)

def _check(callback):
    if callback:callback()

def answer(doc,body,messages,research_plan=None,on_event=None,check_cancel=None):
    sources,attached,memories=scope(doc)
    current=next((n for n in doc['nodes'] if n['id']==body.node_id),None)
    document_anchor=current is None and body.node_id=='document'
    if document_anchor:
        current={'id':'document','title':doc['title'],'summary':doc.get('subtitle',''),'paragraphs':[],'source_ids':[],'interaction':'none','steps':[]}
    if current is None:raise ValueError('提问位置不属于当前文档')
    selected=body.selected_text or ''
    _check(check_cancel);_notify(on_event,'document_retrieval_started','正在查找当前论文中的相关证据')
    node_matches=retrieval.retrieve([{'id':n['id'],'quote':n['title']+' '+n['summary']+' '+' '.join(n['paragraphs'])} for n in doc['nodes']],body.text+' '+selected,limit=3)
    matching_ids={n['id'] for n in node_matches}
    preferred=set(current['source_ids'])|{sid for n in doc['nodes'] if n['id'] in matching_ids for sid in n['source_ids']}
    evidence=retrieval.retrieve(sources,body.text+' '+selected+' '+current['title'],limit=24,preferred=preferred)
    _notify(on_event,'document_evidence_ready',f'已整理 {len(evidence)} 条论文证据',source_count=len(evidence))
    context={'document_id':doc['id'],'turn_id':str(uuid4())}
    visual=None;visual_image=None
    if body.selected_page:
        _check(check_cancel);_notify(on_event,'visual_read_started',f'正在读取第 {body.selected_page} 页所选区域',page=body.selected_page)
        if not doc.get('file_path') or not 1<=body.selected_page<=doc['page_count']:raise ValueError('所选页码无效')
        prompt=('只输出JSON，字段description字符串、uncertainties字符串数组。根据原页或框选区域回答这个观察问题：'+body.text+
                '。只观察能看清的内容，不猜测模糊数字，说明识别局限。')
        visual_image=parser.page_image(doc['file_path'],body.selected_page,body.bbox)
        visual=gateway.request('vision',gateway.image_message(visual_image,prompt),max_tokens=3000,context=context)
        evidence=retrieval.retrieve(sources,body.text,limit=12,preferred=[s['id'] for s in sources if s['page']==body.selected_page])+evidence[:8]
        evidence=list({s['id']:s for s in evidence}.values())
    searches=[]
    if research_plan:
        for index,question in enumerate(research_plan.get('questions',[])[:4]):
            _check(check_cancel)
            local=retrieval.retrieve(sources,question+' '+current['title'],limit=10,preferred=preferred)
            evidence.extend(local)
            if research_plan.get('use_external_sources') and index<3:
                _notify(on_event,'web_search_started',f'正在为子问题 {index+1} 读取外部学术来源',query=question)
                try:
                    query=gateway.structured('copilot','把检索意图压缩为2至5个准确英文专业术语。不要写Explain/definition/source、site或OR。',
                                             {'query':question,'question':body.text},SearchQuery,max_tokens=300,context=context)['query']
                    found=retrieval.web_search(query,context={**context,'research_question':index+1})
                    searches.append(found);evidence.extend(found['sources'])
                    _notify(on_event,'source_read',f'子问题 {index+1} 已读取 {len(found["sources"])} 个外部来源',source_count=len(found['sources']))
                except Exception as error:
                    searches.append({'query':question,'sources':[],'error':str(error)})
                    _notify(on_event,'source_read','本轮外部取证未获得可读来源',source_count=0)
        evidence=list({s['id']:s for s in evidence}.values())
    input_data={'document':{'id':doc['id'],'title':doc['title']},'current_node':current,'question':body.text,'selected_text':selected,'visual_observation':visual,'attached_documents':attached,'allowed_sources':evidence,'recent_messages':[{'role':m['role'],'text':m['text'],'node_id':m['node_id']} for m in messages[-12:]],'explanation_preferences':memories,'component_state':{'interaction':current.get('interaction'),'steps_count':len(current.get('steps',[])),'current_step':body.current_step},'confirmed_research_plan':research_plan}
    instruction=('回答用户当前问题，不把批判性疑问当作基础薄弱。只有证据支持的具体主张才引用source_ids。'
                 '需要论文之外的专业知识而材料不足时need_external=true并给出精确检索query，先不编造。'
                 '用户明确要求联网或外部权威定义时，必须need_external=true并为选定概念给精确检索query。'
                 '用户明确要求操作当前步骤演示时，可选择next_step/previous_step/reset_steps，否则none。'
                 '只说明原文确实提出的局限，不能为了回答“局限”而臆造作者没说的互斥性、穷尽性、统计要求。'
                 'memory_preference只在用户明确要求长期使用某种解释方式时给简短偏好，否则null。不得写掌握状态。')
    if research_plan:instruction+=' 按用户确认的研究计划组织回答；逐项覆盖子问题，并清楚区分当前论文、附加论文、外部知识和教学解释。'
    _check(check_cancel);_notify(on_event,'answer_composition_started','正在依据已读取证据组织回答')
    result=gateway.structured('copilot',instruction,input_data,Answer,max_tokens=5000,context=context)
    search_result=None
    if result['need_external'] and result['search_query'] and len(searches)<3:
        try:
            _check(check_cancel);_notify(on_event,'web_search_started','回答发现证据缺口，正在补充一次外部取证',query=result['search_query'])
            search_query=gateway.structured('copilot','把检索意图压缩为2至5个准确英文专业术语。去掉site、OR、Explain、definition等指令，不要拼接多个主题。',
                                           {'query':result['search_query'],'question':body.text},SearchQuery,max_tokens=300,context=context)['query']
            search_result=retrieval.web_search(search_query,context=context)
            searches.append(search_result)
            evidence+=search_result['sources'];input_data.update(allowed_sources=evidence,external_search=search_result)
            result=gateway.structured('copilot',instruction+' 已完成一次实际联网读取；只补充实际读取的外部正文支持的知识。'
                                      '如果没有可读外部来源，说明取证不足并限定为本文用法，不从记忆补造形式化定义或推导。'
                                      '区分原文内容、外部知识与教学解释。不能把搜索摘要冒充全文证据。',input_data,Answer,max_tokens=5000,context=context)
        except Exception as error:
            search_result={'sources':[],'error':str(error),'query':result['search_query']}
            result.update(text=result['text']+'\n\n外部取证未完成：'+str(error),need_external=True,source_ids=[],action='none')
    elif result['need_external'] and result['search_query']:
        result.update(text=result['text']+'\n\n本次已达到外部取证轮次上限；仍缺少的证据不作补写。')
    available={s['id'] for s in evidence}
    invalid=set(result['source_ids'])-available
    cited=[s for s in evidence if s['id'] in result['source_ids']]
    _check(check_cancel);_notify(on_event,'answer_review_started','正在对照来源核验回答')
    review=review_answer(result['text'],cited,context,visual_image)
    if invalid:review={'verdict':'insufficient','issues':review['issues']+['回答引用未知来源：'+','.join(invalid)]}
    if not cited:review={'verdict':'insufficient','issues':review['issues']+['缺少可回查引用，作为未核验解释保留']}
    action=None
    explicit_action=bool(re.search(r'切换|推进|前进|后退|重置|从头|继续演示|演示下一步|演示上一步|move to|go to|reset',body.text.lower())) or body.text.strip().lower() in {'下一步','上一步','next','previous'}
    if result['action']!='none' and explicit_action and current.get('interaction')=='stepper' and len(current.get('steps',[]))>=2:
        # Actual execution is acknowledged separately; never claim an unexecuted change.
        action={'id':str(uuid4()),'type':result['action'],'node_id':body.node_id}
    memory=None
    if result['memory_preference']:
        text=result['memory_preference'][:140]
        memory={'id':'preference-'+hashlib.sha256(text.encode()).hexdigest()[:16],'text':text,'kind':'explanation_preference'}
    search_summary={'queries':[s.get('query') for s in searches if s.get('query')],'source_count':sum(len(s.get('sources',[])) for s in searches),'errors':[s.get('error') for s in searches if s.get('error')]} if searches else search_result
    return {'provider':'qwen','model':gateway.settings.models()['copilot'],'text':result['text'],'source_ids':[sid for sid in result['source_ids'] if sid in available],'action':action,'memory':memory,'can_patch':review['verdict']=='supported' and not document_anchor,'verification':review,'external_search':search_summary,'visual_observation':visual},[s for s in evidence if s['kind']=='external']

def expand(doc,concept,question=None):
    sources,_,_=scope(doc)
    query=question or '请进一步解释'+concept['title']+'，从当前定义深入到其原理、成立条件和与论文的连接'
    evidence=retrieval.retrieve(sources,query+' '+concept.get('text',''),limit=12,preferred=concept.get('source_ids'))
    search_query=gateway.structured('copilot','为这个专业知识问题提取一个准确的英文检索短语，2至5个关键术语。不要写Explain/definition/source等指令词，不加site或OR，不写整个问题。',
                                    {'concept':concept['title'],'question':query},SearchQuery,max_tokens=300,context={'document_id':doc['id']})['query']
    search=retrieval.web_search(search_query,context={'document_id':doc['id'],'task':'knowledge_expansion'})
    evidence+=search['sources']
    value=gateway.structured('copilot','围绕用户实际查阅或提问补充一层知识。不能将原文外知识伪装为论文主张。'
                             '每个外部关键定义、公式和条件必须由提供的实际来源支持。若外部证据不足，只解释论文已有定义并明确注明未完成外部取证，不能补造定义。next_question给一个可选的继续深入问题。',
                             {'parent_concept':concept,'question':query,'sources':evidence,'paper_title':doc['title']},Knowledge,skill='knowledge-expansion',max_tokens=5000,context={'document_id':doc['id']})
    ids={s['id'] for s in evidence}
    if not value['source_ids'] or set(value['source_ids'])-ids:raise ValueError('知识补充没有提供有效证据引用')
    verification=review_answer(value['text']+' '+value['why'],[s for s in evidence if s['id'] in value['source_ids']],{'document_id':doc['id']})
    cid='concept-'+hashlib.sha256((doc.get('domain','')+'|'+value['title']+'|'+value['layer']).encode()).hexdigest()[:16]
    return {**value,'id':cid,'next':None,'domain':doc.get('domain',''),'document_id':doc['id'],'node_id':concept.get('node_id'),'verification':verification,'external_search':{k:v for k,v in search.items() if k!='sources'}},search['sources']
