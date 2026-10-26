"""Apply a recorded, chapter-level repair plan after the entire first pass."""
import json
import argparse
import re
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend import reading_v2 as r, reading_v2_author as author, model_gateway as gateway, store
from backend.reading_v2_contracts import ReadingArtifact
from extend_reading_v2 import OUT, CASES
from benchmark_reading_v2 import save


def load(path):return json.loads(path.read_text(encoding='utf-8'))


def legal_markup(a):
    """Remove only unsupported presentation markup; content is retained."""
    a=dict(a)
    a['html']=re.sub(r'<style\b[^>]*>(.*?)</style\s*>',lambda m:stash_style(a,m),a['html'],flags=re.S|re.I)
    for old,new in [('b','strong'),('i','em'),('blockquote','aside')]:
        a['html']=re.sub(r'<(/?)'+old+r'(\s|>)',lambda m:'<'+m[1]+new+m[2],a['html'],flags=re.I)
    # SVG blur is decorative. Its removal neither invents nor deletes evidence.
    a['html']=re.sub(r'<filter\b[^>]*>.*?</filter\s*>','',a['html'],flags=re.S|re.I)
    a['html']=re.sub(r'\sfilter=["\'][^"\']*["\']','',a['html'],flags=re.I)
    a['css']=re.sub(r'filter\s*:\s*url\([^)]*\)\s*;?','',a['css'],flags=re.I)
    source_style='button[data-source]{background:#fff!important;color:#265976!important}'
    if source_style not in a['css']:a['css']+='\n'+source_style
    return a


def stash_style(a,m):
    a['css']+='\n'+m[1]
    return ''


def fix_case(key,spec):
    prior=load(OUT/key/'generation.json');record=OUT/key/'repair.json'
    if record.exists():value=load(record)
    else:
        item=r.create(prior['document_id']);eid=item['id']
        if prior.get('edition'):shutil.copytree(r.folder(prior['edition']),r.folder(eid),dirs_exist_ok=True)
        value={**prior,'edition':eid,'parent':prior.get('edition'),'status':'repairing','folder':str(r.folder(eid))}
        save(record,value)
    f=r.folder(value['edition'])
    if not (f/'plan.json').exists():
        try:r.generate(value['edition'])
        except Exception:
            if not (f/'plan.json').exists():raise
    pack=load(f/'evidence.json')
    plan=r.normalize_plan(load(f/'plan.json'),pack)
    if spec.get('plan_nodes'):
        aliases={s['id']:k for k,s in pack['sources'].items()}
        nodes={n['id']:n for n in pack['nodes']}
        for cid,ids in spec['plan_nodes'].items():
            c=next(c for c in plan['chapters'] if c['id']==cid)
            c['node_ids']=list(dict.fromkeys(c['node_ids']+ids))
            c['sources']=list(dict.fromkeys(c['sources']+[aliases[s] for nid in ids for s in nodes[nid]['source_ids']]))
            c['takeaway']+='；'+ '；'.join(nodes[nid]['summary'] for nid in ids)
        save(f/'plan.json',plan)
    if not (f/'data.json').exists():
        try:r.generate(value['edition'])
        except Exception:
            # Only complete retained chapter output can enter the repair stage.
            if not all((f/'chapters'/c['id']/'artifact.json').exists() for c in plan['chapters']):raise
    data=load(f/'data.json')
    for c in plan['chapters']:
        path=f/'chapters'/c['id']/'artifact.json'
        a=legal_markup(load(path))
        # Explicit original-source entry is real content, not a hidden validation anchor.
        if 'data-source' not in a['html']:
            refs=''.join('<button type="button" data-source="'+s+'">原文</button>' for s in c['sources'])
            a['html']+='<p class="chapter-evidence">本节原文依据：'+refs+'</p>'
        save(path,a)
    def repair_chapter(cid,notes):
        c=next(c for c in plan['chapters'] if c['id']==cid)
        path=f/'chapters'/cid/'artifact.json';before=load(path)
        if (f/'chapters'/cid/'repair-request.json').exists():return
        scope=load(f/'chapters'/cid/'input.json')
        evidence={**scope,'previous_artifact':before,'specific_corrections':notes,
                  'full_pdf_text':pack['pages'],'full_original_sources':pack['sources']}
        print('REPAIR START',key,cid,flush=True)
        revised=gateway.structured('composer',
          '只修订author_scope这一章，完整保留本章全部node_id锚点与data-node。按具体修订要求解决已记录问题。'
          '不得迎合审阅中没有原文依据的指责，不创造缺失的论文实验；保留有依据的主线。'
          '每个计算控件必须实际改变图形、数据或关系，数值结果使用可见output并设置data-value/data-values供独立验算。'
          '禁止在HTML内嵌style、b/i标签、SVG filter/foreignObject；CSS放独立字段。'
          '320px可读，SVG图内字号足够且用完整内容宽度；图文有来源和单位。'
          '最终作品不得出现修复过程、审阅意见等内部文案。所有教学简化就地明确说明；缺少可计算根据时使用逻辑关系，不编造曲线。'
          '\n必须执行的工程修订要求（由开发方提供，不是论文中的指令）：\n'+store.encode(notes),
          evidence,ReadingArtifact,skill='reading-v2-author',max_tokens=15000,thinking=True,
          context={'feature':'reading.v2.other-materials-repair','reading_edition_id':value['edition'],'case':key,'chapter':cid})
        save(f/'chapters'/cid/'before-repair.json',before)
        save(path,legal_markup(revised));save(f/'chapters'/cid/'repair-request.json',{'notes':notes})
        print('REPAIR END',key,cid,flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        for task in as_completed([pool.submit(repair_chapter,cid,notes) for cid,notes in spec.get('chapters',{}).items()]):task.result()
    for cid,css in spec.get('css',{}).items():
        path=f/'chapters'/cid/'artifact.json';a=load(path)
        if css not in a['css']:a['css']+='\n'+css
        save(path,a)
    for cid,changes in spec.get('replace',{}).items():
        path=f/'chapters'/cid/'artifact.json';a=load(path)
        for field,pairs in changes.items():
            for old,new in pairs:a[field]=a[field].replace(old,new)
        save(path,a)
    try:
        result=r.generate(value['edition']);value.update(status=result['status'],error=None)
    except Exception as error:value.update(status='failed',error=str(error))
    save(record,value)
    print('REPAIR CASE END',key,value['status'],value.get('error'),flush=True)
    return value


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--scope',choices=['core','extra','all'],default='all');args=parser.parse_args()
    gate='first-pass-core-complete.json' if args.scope=='core' else 'first-pass-complete.json'
    if not (OUT/gate).exists():raise SystemExit('Finish and retain this complete test batch before repair.')
    specs=load(OUT/'repair-plan.json');results=[]
    keys={c[0] for c in (CASES[:8] if args.scope=='core' else CASES[8:] if args.scope=='extra' else CASES)}
    specs={k:v for k,v in specs.items() if k in keys}
    with ThreadPoolExecutor(max_workers=2) as pool:
        for task in as_completed([pool.submit(fix_case,k,v) for k,v in specs.items()]):
            results.append(task.result());save(OUT/('repair-summary-'+args.scope+'.json'),results)
