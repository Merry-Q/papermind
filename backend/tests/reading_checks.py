"""Offline quality checks; never called by the product generation pipeline."""
import re
from backend.reading_v2 import MarkupCheck, external_url
from backend.reading_v2_contracts import ReadingArtifact

def check_plan(plan,doc,pack):
    known={n['id'] for n in doc['nodes']}
    covered={n for c in plan['chapters'] for n in c['node_ids']}
    if covered!=known: raise ValueError('全文节点覆盖不完整或越界：'+str(known^covered))
    refs={s for c in plan['chapters'] for s in c['sources']}
    if refs-set(pack['sources']): raise ValueError('计划引用来源不存在')
    if any(p<1 or p>doc['page_count'] for p in plan['visual_pages']): raise ValueError('原页范围越界')

def validate_artifact(artifact,doc,data):
    ReadingArtifact.model_validate(artifact)
    check=MarkupCheck(data);check.feed(artifact['html'])
    missing={n['id'] for n in doc['nodes']}-check.ids
    if missing:check.errors.append('缺少节点锚点：'+str(missing))
    if (not check.refs and 'data-source' not in artifact['javascript']) or check.refs-set(data['sources']):check.errors.append('来源缺失或越界')
    script_refs=set(re.findall(r'''["'](S\d{3,})["']''',artifact['javascript']))
    if script_refs-set(data['sources']):check.errors.append('动态来源ID越界：'+str(script_refs-set(data['sources'])))
    if re.search(r'@import',artifact['css'],re.I) or external_url(artifact['css']):check.errors.append('CSS不允许外部资源')
    if re.search(r'</(?:script|style)',artifact['javascript']+artifact['css'],re.I):check.errors.append('产物终止标签不允许')
    forbidden=r'\b(?:fetch|XMLHttpRequest|WebSocket|EventSource|localStorage|sessionStorage|indexedDB|eval|Worker|SharedWorker)\s*(?:\(|\.)|\bnew\s+Function\b|\bimport\s*(?:\(|\s)|\b(?:window|globalThis|self)\s*\.\s*(?:parent|top|opener|location)|\b(?:parent|top|opener)\s*\.\s*postMessage|\bdocument\s*\.\s*(?:cookie|write)|\blocation\s*\.'
    if re.search(forbidden,artifact['javascript']):check.errors.append('脚本包含外部访问或动态执行')
    if check.errors:raise ValueError('；'.join(check.errors))
    return {'status':'pass','anchors':len(doc['nodes']),'citations':len(check.refs)}


def ref_issues(node,source_ids):
    issues=[]
    if not node['source_ids']:issues.append('节点没有引用')
    refs=set(node['source_ids'])|{r for c in node['claims'] for r in c['source_ids']}|{r for step in node['steps'] for r in step['source_ids']}|{r for term in node['terms'] for r in term['source_ids']}
    missing=refs-source_ids
    if missing:issues.append('未知来源ID：'+','.join(sorted(missing)))
    if node['interaction']=='stepper' and len(node['steps'])<2:issues.append('步骤演示缺少有效步骤')
    return issues


