"""Finish evidence-backed fixes and rebuild drafts with scoped dynamic lookup."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend import reading_v2 as r
from extend_reading_v2 import OUT
from benchmark_reading_v2 import save

def load(p):return json.loads(p.read_text(encoding='utf-8'))
def edit(key,cid,fn):
    v=load(OUT/key/'repair.json');p=r.folder(v['edition'])/'chapters'/cid/'artifact.json'
    a=load(p)
    if not p.with_name('before-engineering-final.json').exists():save(p.with_name('before-engineering-final.json'),a)
    fn(a);save(p,a)

def simulation(a):
    v=load(OUT/'simulation-argument/repair.json');f=r.folder(v['edition'])
    plan=r.normalize_plan(load(f/'plan.json'),load(f/'evidence.json'))
    c=next(c for c in plan['chapters'] if c['id']=='ch-conclusion')
    refs=''.join('<button type="button" data-source="'+s+'">原文</button>' for s in c['sources'])
    a['html']='''<section id="core-trilemma" data-node="core-trilemma"><h2>至少一条成立，并不等于已经知道哪条成立</h2>
<p>在基底独立性、模拟所需算力及同类观察者参照类等前提下，作者提出三分论证：以下三种解释中至少一种接近成立。它们不是由这篇论文测量出的现实概率，也不自动构成互斥的三分类。</p>
<ol class="branch-statements"><li><strong>P1：前人类阶段的终止</strong><p>人类文明极可能在达到后人类阶段前灭绝。</p></li><li><strong>P2：极少祖先模拟</strong><p>后人类文明极不可能运行大量祖先模拟。</p></li><li><strong>P3：模拟中的观察者</strong><p>在相应观察者比例及无额外区分信息的前提下，我们几乎肯定处于模拟中。</p></li></ol>
<h3>操作推演假设，查看剩余关系</h3><p>勾选仅表示暂定某一分支不成立，不表示现实中已找到排除它的证据。</p>
<div class="branch-controls"><label><input type="checkbox" id="branch-exclude-1">暂定 P1 不成立</label><label><input type="checkbox" id="branch-exclude-2">暂定 P2 不成立</label><label><input type="checkbox" id="branch-exclude-3">暂定 P3 不成立</label><button type="button" id="branch-reset">恢复全部分支</button></div>
<svg class="branch-graph" viewBox="0 0 600 170" aria-label="至少一项成立与三个分支的关系图"><text x="300" y="30" text-anchor="middle" font-size="24">至少一项成立</text><g id="branch-path-1"><path d="M300 45L100 105" stroke="#265976" stroke-width="3"/><circle cx="100" cy="130" r="28" fill="#edf2f1"/><text x="100" y="138" text-anchor="middle" font-size="25">P1</text></g><g id="branch-path-2"><path d="M300 45L300 105" stroke="#265976" stroke-width="3"/><circle cx="300" cy="130" r="28" fill="#edf2f1"/><text x="300" y="138" text-anchor="middle" font-size="25">P2</text></g><g id="branch-path-3"><path d="M300 45L500 105" stroke="#265976" stroke-width="3"/><circle cx="500" cy="130" r="28" fill="#edf2f1"/><text x="500" y="138" text-anchor="middle" font-size="25">P3</text></g></svg>
<output id="branch-result" aria-live="polite"></output><p>图示只做条件推演。若同时暂定三条均不成立，这组假设就与“至少一条成立”的论证前提冲突；不能据此计算一个现实概率。</p>'''+refs+'''</section>
<section id="credence-allocation" data-node="credence-allocation"><h2>从分支关系到个人置信度，还需要额外前提</h2><p>作者讨论了在缺少有区分力的信息时，如何在三种解释之间分配信任。均衡分配是文中讨论的哲学立场，不是实验得到的三组频率；存在有区分力的信息时，判断也依赖这些信息的真实性及其与各分支的关系。</p><p>本页不根据关键词、陨石故事或用户的一次选择生成置信度。平淡无奇原则将同类观察者中模拟者的比例转成个人置信度，也依赖参照类和没有额外区分信息的条件。</p><p>作者的最终条件推论是：除非我们现在生活在模拟中，否则后代几乎不会运行祖先模拟。它不能被简化为“论文证明现实是模拟”。</p>'''+refs+'</section>'
    a['css']='''.branch-controls{display:flex;flex-wrap:wrap;gap:16px;margin:24px 0}.branch-controls label{display:flex;align-items:center;gap:8px}.branch-statements{padding-left:24px}.branch-statements li{margin:20px 0}.branch-graph{display:block;width:100%;max-width:720px;margin:28px auto}#branch-result{display:block;font-size:18px;line-height:1.8;padding:20px 0;border-block:1px solid var(--line)}'''
    a['javascript']='''(()=>{const boxes=[1,2,3].map(i=>document.getElementById('branch-exclude-'+i)),result=document.getElementById('branch-result');function render(){const remaining=[];boxes.forEach((b,j)=>{document.getElementById('branch-path-'+(j+1)).setAttribute('opacity',b.checked?'.15':'1');if(!b.checked)remaining.push('P'+(j+1));});result.dataset.values=JSON.stringify(remaining);result.textContent=remaining.length===3?'目前只能说至少一项成立；还不能决定是哪一项。':remaining.length===0?'这组假设与“至少一项成立”相冲突，需要重新检查所作假设。':remaining.length===1?'在这些推演假设及论证前提下，剩余分支 '+remaining[0]+' 须成立。':'在这些推演假设下，至少 '+remaining.join(' 或 ')+' 中的一项成立。';}boxes.forEach(b=>b.addEventListener('change',render));document.getElementById('branch-reset').addEventListener('click',()=>{boxes.forEach(b=>b.checked=false);render();});render();})();'''
    a['teaching_assumptions']=['分支排除只是用户暂定的逻辑假设，不是新的现实证据或概率估计。']
    a['limitations']=['论证依赖意识、计算与观察者参照类等前提，本文没有实证测量现实的模拟概率。']

edit('simulation-argument','ch-conclusion',simulation)

def moral(a):
    a['html']=a['html'].replace('此选择主要体现了维度','本教学场景关注的维度')
edit('moral-machine','methodology_mm',moral)

def scope_note(a):
    if 'class="excerpt-scope"' not in a['html']:a['html']='<p class="excerpt-scope">阅读范围：仅上传的 Transformer 架构单页，含第3.1节及第3.2节开头；未上传章节的公式与实验不作为本页原文事实。</p>'+a['html']

for record in OUT.glob('*/repair.json'):
    v=load(record)
    if v['status']!='draft' or v['case']=='shannon' or v.get('engineering_final_at'):continue
    f=r.folder(v['edition'])
    for p in f.glob('chapters/*/artifact.json'):
        a=load(p)
        a['css']+='\n.katex{display:inline-block;max-width:100%;overflow-x:auto;vertical-align:middle}.step-controls,.control-buttons{flex-wrap:wrap} @media(max-width:480px){.metric-card,.stat-card{min-width:0}}'
        save(p,a)
    if v['case']=='transformer-excerpt':
        plan=load(f/'plan.json');edit('transformer-excerpt',plan['chapters'][0]['id'],scope_note)
    result=r.generate(v['edition']);v.update(status=result['status'],error=None,engineering_final_at=r.now());save(record,v)
    print('RECOMPOSED',v['case'],v['edition'],flush=True)
