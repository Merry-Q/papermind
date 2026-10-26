"""Deterministic source/math corrections after the recorded author repair pass."""
import json
import re
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend import reading_v2 as r,store
from extend_reading_v2 import OUT
from benchmark_reading_v2 import save

v=json.loads((OUT/'shannon/repair.json').read_text(encoding='utf-8'))
assert v['status']=='draft'
f=r.folder(v['edition'])

def edit(cid,fn):
    p=f/'chapters'/cid/'artifact.json';a=json.loads(p.read_text(encoding='utf-8'))
    before=p.with_name('before-engineering-final.json')
    if not before.exists():save(before,a)
    fn(a);save(p,a)

CSS='''
.telegraph-controls{display:flex;flex-wrap:wrap;gap:18px;margin:24px 0}.telegraph-controls label{display:grid;gap:6px}
.telegraph-results{display:flex;gap:28px;flex-wrap:wrap;margin:20px 0}.telegraph-results output{display:block;font:26px Georgia,serif;font-variant-numeric:tabular-nums;color:var(--accent)}
.telegraph-plot{width:100%;height:auto}.telegraph-note{font-size:14px;color:var(--muted)}.telegraph-equation{overflow-x:auto;max-width:100%;padding:16px 0}
'''

HTML=r'''
<section id="discrete-noiseless-capacity" data-node="discrete-noiseless-capacity">
<h2>符号相同，允许连接的方式不同，容量也会变</h2>
<p>离散无噪信道的容量衡量可区分信号随时间增长的速率：$C=\lim_{T\to\infty}\log_2 N(T)/T$。$N(T)$ 只数允许发送的序列，既取决于符号时长，也取决于连接约束；容量是理论上限，实际信息率还取决于信源。</p>
<p>上传原文的电报例子含点、划、字母空格和词空格，持续时间分别为 2、4、3、6 个时间单位；两个空格不能连续。无约束时可以直接将各符号的 $X^{-t_i}$ 相加，有状态约束时须从允许的状态转移求特征根。</p>
<div class="telegraph-controls">
<label for="telegraph-mode">允许的连接<select id="telegraph-mode"><option value="constrained">原文规则：空格不可连续</option><option value="free">教学对照：任意连接</option></select></label>
<label for="telegraph-dot">点的时长<input id="telegraph-dot" type="number" min="1" max="10" step="1" value="2"></label>
<label for="telegraph-dash">划的时长<input id="telegraph-dash" type="number" min="1" max="10" step="1" value="4"></label>
<label for="telegraph-letter">字母空格时长<input id="telegraph-letter" type="number" min="1" max="10" step="1" value="3"></label>
<label for="telegraph-word">词空格时长<input id="telegraph-word" type="number" min="1" max="10" step="1" value="6"></label>
<button type="button" id="telegraph-reset">恢复原文设置</button></div>
<p class="telegraph-note">原文默认设置可回查；其他时长及无约束模式为教学对照。对数底为2，所有结果以相同时间单位计。</p>
<svg class="telegraph-plot" viewBox="0 0 620 180" aria-label="两个状态及其允许转移"><defs><marker id="telegraph-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10Z" fill="#265976"/></marker></defs><rect x="30" y="55" width="200" height="55" rx="4" fill="#edf2f1"/><text x="50" y="88" font-size="17">上一符号为点或划</text><rect x="390" y="55" width="200" height="55" rx="4" fill="#edf2f1"/><text x="420" y="88" font-size="17">上一符号为空格</text><path d="M230 70L385 70" stroke="#265976" marker-end="url(#telegraph-arrow)"/><text x="260" y="52" font-size="15">发送空格</text><path d="M390 100L235 100" stroke="#265976" marker-end="url(#telegraph-arrow)"/><text x="260" y="132" font-size="15">发送点或划</text><text x="35" y="155" font-size="15">点/划后仍可接点/划</text><text id="telegraph-space-rule" x="390" y="155" font-size="15"></text></svg>
<div class="telegraph-equation"><output id="telegraph-equation"></output></div>
<div class="telegraph-results"><div>最大正根 X<output id="telegraph-root"></output></div><div>容量（bits/时间单位）<output id="telegraph-capacity"></output></div><div>恰好20单位时长的序列数<output id="telegraph-count"></output></div></div>
<svg class="telegraph-plot" viewBox="0 0 620 240" aria-label="允许序列数量的对数随时长变化"><line x1="45" y1="200" x2="595" y2="200" stroke="#596877"/><line x1="45" y1="20" x2="45" y2="200" stroke="#596877"/><path id="telegraph-curve" fill="none" stroke="#265976" stroke-width="3"/><text x="45" y="228" font-size="15">0</text><text x="530" y="228" font-size="15">时长 40</text><text id="telegraph-y-label" x="45" y="16" font-size="15"></text></svg>
<p class="telegraph-note">图中只绘存在序列的时长，纵轴为 log₂ N(T)，不是实验性能曲线。有限时长的计数可以起伏，容量描述渐近增长率。</p>
<p>原文默认规则导出 $X^{-2}+X^{-4}+X^{-5}+X^{-7}+X^{-8}+X^{-10}=1$，因此 $C\approx0.539$。一般点、划时长 d、h，空格时长 l、w 时，方程为 $(X^{-d}+X^{-h})(1+X^{-l}+X^{-w})=1$；无约束教学对照则为 $X^{-d}+X^{-h}+X^{-l}+X^{-w}=1$。</p>
<p>更一般的有限状态信道可由状态转移的行列式方程求容量（原文定理1）。这些结论讨论无噪信道，并不替代后文含噪信道的编码条件。</p>
SOURCE_BUTTONS
</section>'''

JS=r'''
(()=>{const ids=['dot','dash','letter','word'],fields=ids.map(id=>document.getElementById('telegraph-'+id)),mode=document.getElementById('telegraph-mode');
const out=(id,v,text)=>{const el=document.getElementById(id);el.dataset.value=String(v);el.textContent=text??String(v);};
function render(){const [d,h,l,w]=fields.map(e=>Math.min(10,Math.max(1,Math.round(Number(e.value)||1)))),free=mode.value==='free';
const fn=x=>{const a=x**(-d)+x**(-h),b=x**(-l)+x**(-w);return free?a+b-1:a*(1+b)-1;};let lo=1,hi=4;for(let j=0;j<90;j++){const mid=(lo+hi)/2;if(fn(mid)>0)lo=mid;else hi=mid;}const root=(lo+hi)/2,c=Math.log2(root);
let A=Array(41).fill(0),B=Array(41).fill(0),N=Array(41).fill(0);A[0]=N[0]=1;const at=(arr,t)=>t>=0?arr[t]:0;
for(let t=1;t<=40;t++){if(free){N[t]=[d,h,l,w].reduce((s,k)=>s+at(N,t-k),0);}else{A[t]=at(N,t-d)+at(N,t-h);B[t]=at(A,t-l)+at(A,t-w);N[t]=A[t]+B[t];}}
out('telegraph-root',root,root.toFixed(6));out('telegraph-capacity',c,c.toFixed(6));out('telegraph-count',N[20],N[20].toLocaleString('en-US'));
document.getElementById('telegraph-equation').textContent=free?`X⁻${d} + X⁻${h} + X⁻${l} + X⁻${w} = 1`:`(X⁻${d} + X⁻${h}) · (1 + X⁻${l} + X⁻${w}) = 1`;
const rule=document.getElementById('telegraph-space-rule');rule.textContent=free?'允许再次发送空格':'禁止连续空格';rule.setAttribute('fill',free?'#265976':'#ad472d');
const ymax=Math.max(1,...N.filter(n=>n>0).map(n=>Math.log2(n)));let path='';N.forEach((n,t)=>{if(n>0)path+=(path?'L':'M')+(45+550*t/40)+','+(200-170*Math.log2(n)/ymax);});document.getElementById('telegraph-curve').setAttribute('d',path);document.getElementById('telegraph-y-label').textContent='log₂ N(T)，当前上限 '+ymax.toFixed(1);}
fields.forEach(e=>e.addEventListener('input',render));mode.addEventListener('change',render);document.getElementById('telegraph-reset').addEventListener('click',()=>{[2,4,3,6].forEach((v,i)=>fields[i].value=String(v));mode.value='constrained';render();});render();})();
'''

def telegraph(a):
    plan=r.normalize_plan(json.loads((f/'plan.json').read_text(encoding='utf-8')),json.loads((f/'evidence.json').read_text(encoding='utf-8')))
    c=next(c for c in plan['chapters'] if c['id']=='ch3-discrete-capacity')
    buttons=''.join('<button type="button" data-source="'+s+'">原文</button>' for s in c['sources'])
    a.update(html=HTML.replace('SOURCE_BUTTONS',buttons),css=CSS,javascript=JS,
      teaching_assumptions=['无约束模式与可调时长为教学对照；默认受约束电报设置来自原PDF第3至4页。'],limitations=['只讨论有限状态无噪信道，有限时长序列计数不等于实际通信吞吐。'])
edit('ch3-discrete-capacity',telegraph)

def typical(a):
    s=a['javascript']
    s=s.replace('Math.ceil(n * (Q - EPSILON))','Math.max(0, Math.ceil(n * (Q - EPSILON / Math.abs(log2((1-Q)/Q))) - 1e-12))')
    s=s.replace('Math.floor(n * (Q + EPSILON))','Math.min(n, Math.floor(n * (Q + EPSILON / Math.abs(log2((1-Q)/Q))) + 1e-12))')
    a['javascript']=s
    a['html']=a['html'].replace('典型容差 $\\epsilon=0.1$','每符号自信息容差 $\\epsilon=0.1$ bits')
    a['html']=a['html'].replace('局限与条件','<span>独立同分布教学例中，平均每符号码长满足所示界限；一般相关信源须先使用块熵 H(X₁,…,Xₙ)/n，再取熵率极限。</span></h3><h3>局限与条件',1) if '<h3>局限与条件' in a['html'] else a['html']
    # Repair the inserted heading without nesting markup in a heading label.
    a['html']=a['html'].replace('<h3><span>','<p><span>').replace('</span></h3><h3>局限与条件','</span></p><h3>局限与条件')
edit('ch5-noiseless-theorem',typical)

def bsc(a):
    a['html']=a['html'].replace('R = H(Y) − H(Y|X) = H(X) + H(Y|X) − H(Y|X) 的等价形式','R = H(Y) − h₂(p) = H(X) − H(X|Y)')
    a['html']=a['html'].replace('数值误差微小才 clamp，不以 max(0, H(X)−h₂(p)) 替代公式。','输入分布改变实际互信息；容量由当前信道决定。')
edit('ch6-noisy-capacity',bsc)

def peak(a):
    a['html']=a['html'].replace('界限收敛演示','峰值功率的可证范围')
    a['html']=a['html'].replace('所有函数 $f(t)$ 的瞬时值均不超过常数 $S$','所有函数的瞬时功率 $|f(t)|^2$ 均不超过常数 $S$')
    a['html']=re.sub(r'<p>随着峰值功率.*?</p>', '<p>高信噪比下，所示下界与通用上界具有相同的主导对数增长，但绝对间距不必趋零。原文另指出：当 S/N 趋于0，且频带从0开始时，C / [W log₂(1+S/N)] 趋于1。两种极限的条件不能混用。</p>',a['html'],flags=re.S)
    a['html']=a['html'].replace('"For sufficiently large S/N... C ~ W log(1 + S/N)"','原文分别给出高信噪比界限与低信噪比极限。')
edit('ch9-peak-power',peak)

# Numeric results are semantic, visible outputs; no hidden acceptance values.
for p in f.glob('chapters/*/artifact.json'):
    a=json.loads(p.read_text(encoding='utf-8'))
    a['html']=re.sub(r'<span([^>]*\bid="(?:stat-[^"]+|nm-[^"]+-val|val-lower|val-upper|val-error|rate-result|entropy-value|redundancy-value)"[^>]*)>(.*?)</span>',r'<output\1>\2</output>',a['html'],flags=re.S)
    a['html']=a['html'].replace('教学示例，非论文训练权重','教学示例，不是论文测量数据')
    a['css']+='\n.katex{display:inline-block;max-width:100%;overflow-x:auto;vertical-align:middle} @media(max-width:480px){.stats-grid,.results-grid,.stat-grid{grid-template-columns:1fr}.rd-section,.interaction-panel{padding:14px}}'
    save(p,a)
result=r.generate(v['edition']);v.update(status=result['status'],error=None,engineering_final_at=r.now());save(OUT/'shannon/repair.json',v)
print('Shannon deterministic corrections composed',v['edition'])
