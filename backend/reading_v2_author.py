"""Shared document direction, independently cached chapter authors, one edition."""
from concurrent.futures import ThreadPoolExecutor
import html
import json
from . import model_gateway as gateway, store
from .reading_v2_contracts import ReadingArtifact
from .reading_v2_markup import normalize

BASE_CSS='''
:root{--ink:#233342;--muted:#596877;--accent:#265976;--warm:#ad472d;--line:#d6dcd9;--paper:#fcfbf8;--soft:#edf2f1}
body{background:var(--paper);color:var(--ink);font-family:"Microsoft YaHei",system-ui,sans-serif;font-size:16px;line-height:1.95}
.paper-reading{max-width:1120px;margin:auto;padding:40px clamp(18px,5vw,58px) 80px;overflow-wrap:anywhere}
.paper-reading h1{font:normal clamp(32px,5vw,58px)/1.12 Georgia,"Noto Serif SC",serif;letter-spacing:-.025em;margin:18px 0 26px;text-wrap:balance}
.paper-reading h2{font-size:clamp(25px,3.5vw,34px);font-weight:500;line-height:1.4;margin:0 0 20px;text-wrap:balance}
.paper-reading h3{font-size:20px;font-weight:500;line-height:1.5}.paper-reading p{margin:12px 0 18px}
.paper-hero{padding:16px 0 38px;border-bottom:1px solid var(--line)}
.paper-hero .paper-thesis{font-size:18px;line-height:1.95;max-width:55ch}.paper-hero nav{display:flex;flex-wrap:wrap;gap:8px 22px;margin:26px 0 0}
.paper-hero nav a{font-size:13px;color:var(--accent);text-decoration:underline;text-underline-offset:6px}
.paper-chapter{padding:48px 0 34px;border-bottom:1px solid var(--line);min-width:0}
.paper-chapter :where(section,article,div,figure,fieldset){min-width:0}
.paper-chapter :where(table){display:block;max-width:100%;overflow:auto}
.paper-chapter :where(pre){white-space:pre-wrap;overflow-wrap:anywhere}
.paper-reading button{border:1px solid var(--line);background:transparent;color:var(--accent);padding:8px 14px;min-height:38px;border-radius:4px;font-size:13px;line-height:1.5}
.paper-reading button:hover{background:var(--soft)}.paper-reading button:disabled{opacity:.5;cursor:default}
.paper-reading input[type=range]{accent-color:var(--accent);max-width:100%;min-width:0}.paper-reading input[type=number]{width:90px}
.paper-reading select,.paper-reading input[type=number]{padding:7px 9px;border:1px solid var(--line);background:var(--paper);color:var(--ink);font-size:14px;border-radius:4px;max-width:100%}
.paper-reading input[type=checkbox]{accent-color:var(--warm)}.paper-reading label{font-size:14px;line-height:1.7}
.paper-reading svg,.paper-reading canvas{display:block;max-width:100%;height:auto}
.paper-reading details{padding:14px 0;border-top:1px solid var(--line);margin-top:20px}.paper-reading summary{cursor:pointer;color:var(--accent);font-size:14px}
.paper-reading table{width:100%;border-collapse:collapse;font-size:13px;font-variant-numeric:tabular-nums}
.paper-reading th,.paper-reading td{padding:9px 7px;text-align:left;border-bottom:1px solid var(--line)}
.paper-reading button[data-source]{font-size:12px;color:var(--accent);border:0;padding:6px 0;margin-right:16px;text-decoration:underline;text-underline-offset:4px}
.paper-reading ::selection{background:#f3d5ac;color:#233342}.paper-reading :focus-visible{outline:2px solid var(--accent);outline-offset:4px}
.paper-reading .reading-limitations{font-size:14px;color:var(--muted);padding-top:28px}.paper-reading .reading-limitations h2{font-size:24px}
@media(max-width:480px){.paper-reading{padding-top:24px}.paper-chapter{padding-top:32px}.paper-hero .paper-thesis{font-size:16px}.paper-reading{font-size:15px}.paper-reading h2{font-size:25px}.paper-reading table{font-size:12px}}
'''

def compose(f,plan,pack,data,interface,context,cached,checkpoint=lambda:None):
    node_map={n['id']:n for n in pack['nodes']}
    interface=interface or {}
    def author(chapter):
        checkpoint()
        sf=f/'chapters'/chapter['id'];sf.mkdir(parents=True,exist_ok=True)
        nodes=[node_map[n] for n in chapter['node_ids']]
        canonical={s for n in nodes for s in n['source_ids']}
        planned=set(chapter['sources'])
        sources={k:v for k,v in pack['sources'].items() if v['id'] in canonical or k in planned}
        pages={s['page'] for s in sources.values()}
        # Evidence chapters may compare a table that lies beyond a node's brief quote.
        if chapter['basis'] in {'paper','mixed'}:pages.update(t['page'] for t in data['tables'])
        scoped_data=data
        keys=['note']
        if 'scaled-dot-product' in chapter['node_ids']:keys+=['attention','heads']
        if 'positional-encoding' in chapter['node_ids']:keys+=['position']
        if 'complexity-analysis' in chapter['node_ids']:keys+=['complexity']
        if 'mt-results' in chapter['node_ids'] or 'ablation-studies' in chapter['node_ids']:keys+=['results']
        acceptance={k:interface[k] for k in keys if k in interface}
        # Each evidence chapter only implements the subset matching its own nodes.
        if 'results' in acceptance:
            acceptance['scope_note']='只实现本scope负责的实验：mt-results实现result-task与BLEU图；ablation-studies实现ablation-config/result。不要重复其他scope的控件。'
        payload={'author_scope':chapter,'document_title':pack['title'],'art_direction':plan['art_direction'],
                 'shared_design':'遵循整篇art_direction，自选适合材料的机制图、证据比较或论证关系。宿主提供基础字体、按钮和间距，CSS写本章构图，不用重复卡片网格。',
                 'nodes':nodes,'sources':sources,'original_pages':[p for p in pack['pages'] if p['page'] in pages],
                 'runtime_data':scoped_data,'acceptance_interface':acceptance}
        (sf/'input.json').write_text(store.encode(payload),encoding='utf-8')
        instruction=('只创作author_scope指定章节。必须实现acceptance_interface中的真实输入、输出数据属性与视觉联动；其优先级高于早期plan中的建议，不能改ID、缺省值或计算公式。不要生成其他章节，也不生成整篇标题。'
                     '本章所有node_id都要成为实际存在的锚点；先解决完整内容与行为，再完成视觉。来源必须从本章sources挑选且真正支持所述。'
                     '实验表格必须直接从window.paperMindData.tables取值，不手写mock数据；表格值为字符串，可用Number读十进制，成本科学计数另处理；null不能算成0。'
                     '按本篇真实论证选择互动形式；不套用其他论文的表号、实验、维度或结论。没有实证数据就展示逻辑与条件，不编造数值曲线。'
                     '先按原公式独立检查默认值与输入边界；图形、表头、单位、解释与计算结果必须一致。教学参数明确标注，不捏造硬件阈值。'
                     '所有控件有label；默认显示完整核心关系。来源按钮由内核处理，不自行添加占位行为。')
        artifact=cached(sf/'artifact.json',lambda:gateway.structured('composer',instruction,payload,ReadingArtifact,skill='reading-v2-author',max_tokens=15000,thinking=True,context={**context,'chapter':chapter['id']}))
        return chapter,artifact
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(author,c) for c in plan['chapters']]
        results=[];errors=[]
        for future in futures:
            try:results.append(future.result())
            except Exception as e:errors.append(str(e))
    if errors:raise ValueError('章节生成失败：'+'；'.join(errors))
    fragments=[];styles=[BASE_CSS];scripts=[];assumptions=[];limits=[]
    for chapter,a in results:
        # Exact source aliases also apply to citations constructed by scene scripts.
        a=dict(a)
        for alias,source in sorted(data['sources'].items(),key=lambda pair:len(pair[1]['id']),reverse=True):
            for field in ['html','javascript']:
                a[field]=a[field].replace(source['id'],alias)
        a=normalize(a,chapter['node_ids'],chapter['id'],namespace=not bool(interface))
        wrapper='chapter-'+chapter['id']
        fragments.append(f'<div class="paper-chapter" id="{wrapper}">'+a['html']+'</div>')
        styles.append('@scope (#'+wrapper+'){'+a['css']+'}')
        # Common class selectors in independently authored chapters cannot touch peers.
        scoped='''(()=>{const root=document.getElementById(ROOT_ID);const d=new Proxy(document,{get(t,k){if(k==='addEventListener'||k==='removeEventListener')return(type,...args)=>(type==='DOMContentLoaded'?t:root)[k](type,...args);if(k==='querySelector')return s=>root.querySelector(s);if(k==='querySelectorAll')return s=>root.querySelectorAll(s);if(k==='getElementById')return id=>{const key=String(id);return root.id===key?root:(root.querySelector('[id="'+CSS.escape(key)+'"]')||root.querySelector('[id="'+CSS.escape(PREFIX+key)+'"]'));};if(k==='body'||k==='documentElement')return root;const v=Reflect.get(t,k,t);return typeof v==='function'?v.bind(t):v;}});((document)=>{SCRIPT})(d);})();'''
        scripts.append(scoped.replace('ROOT_ID',json.dumps(wrapper)).replace('PREFIX',json.dumps(chapter['id']+'--' if not interface else '')).replace('SCRIPT',a['javascript']))
        assumptions+=a['teaching_assumptions'];limits+=a['limitations']
    nav=''.join('<a href="#'+c['node_ids'][0]+'">'+html.escape(c['title'])+'</a>' for c in plan['chapters'])
    overview=''
    if (f/'overview.json').exists():
        visual=json.loads((f/'overview.json').read_text(encoding='utf-8'))
        overview='<div id="document-overview">'+visual['html']+'</div>'
        styles.append('@scope (#document-overview){'+visual['css']+'}')
        scripts.insert(0,visual['javascript'])
    intro='<header class="paper-hero"><h1>'+html.escape(pack['title'])+'</h1><p class="paper-thesis">'+html.escape(plan['thesis'])+'</p>'+overview+'<nav aria-label="讲解章节">'+nav+'</nav></header>'
    end='<footer class="reading-limitations"><h2>带着边界理解这篇论文</h2>'+''.join('<p>'+html.escape(v)+'</p>' for v in plan['boundaries'])+'</footer>'
    return {'title':pack['title']+' · paperMind 交互讲解','description':plan['reading_path'],'html':'<main class="paper-reading">'+intro+''.join(fragments)+end+'</main>','css':'\n'.join(styles),'javascript':'\n'.join(scripts),'teaching_assumptions':list(dict.fromkeys(assumptions)),'limitations':list(dict.fromkeys(limits))}
