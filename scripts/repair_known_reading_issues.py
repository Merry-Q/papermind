"""Source-backed corrections to cloned drafts; never edits first-pass evidence."""
import json
from pathlib import Path
import re
import shutil
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend import reading_v2 as r,store

OUT=store.ROOT/'artifacts/reading-v2/known-issues-repair'
EDITIONS=json.loads((OUT/'editions.json').read_text(encoding='utf-8'))
CSS='''
.repair-lab{margin:24px 0;padding:24px 0;border-block:1px solid var(--line)}
.repair-controls{display:flex;flex-wrap:wrap;align-items:center;gap:16px;margin:20px 0}
.repair-controls label{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.repair-readout{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,180px),1fr));gap:18px;margin:20px 0}
.repair-readout output{font-size:23px;font-variant-numeric:tabular-nums;display:block;color:var(--accent)}
.repair-note{font-size:14px;color:var(--muted);line-height:1.8}.repair-chart{width:100%;height:auto;overflow:visible}
.repair-bar{display:grid;grid-template-columns:minmax(90px,1fr) 3fr 75px;gap:12px;align-items:center;margin:16px 0;font-size:14px}
.repair-track{background:var(--soft);min-width:0}.repair-fill{height:24px;background:var(--accent);max-width:100%}
@media(max-width:480px){.repair-bar{grid-template-columns:1fr;gap:5px}.repair-controls input{max-width:100%}}
'''


def load(path):return json.loads(path.read_text(encoding='utf-8'))
def write(path,v):path.write_text(store.encode(v),encoding='utf-8')
def chapter(folder,name):return folder/'chapters'/name/'artifact.json'
def replace(folder,name,html,js,assumptions=(),limitations=()):
    write(chapter(folder,name),{'title':name,'description':'原文回查后修订','html':html,'css':CSS,'javascript':js,
         'teaching_assumptions':list(assumptions),'limitations':list(limitations)})
def edit(folder,name,fn):
    path=chapter(folder,name);a=load(path);fn(a);write(path,a)
def source_buttons(ids):return ''.join(f'<button type="button" data-source="{id}">原文</button>' for id in ids)


def sensors():
    folder=r.folder(EDITIONS['adaptive-dcs-somp']['edition'])
    replace(folder,'chap-3-bottleneck',r'''
<section id="sensing-matrix-construction" data-node="sensing-matrix-construction">
<h2>网格更细，矩阵为何迅速变大？</h2>
<p>方位角和仰角分别取 $q_{az}$、$q_{el}$ 个候选点。发射与接收阵列各有 $q_{az}q_{el}$ 组方向，原文给出的感知矩阵列数是 $(q_{az}q_{el})^2$。</p>
<p>原文式 (7)：$\omega^{(0)}[n]=(\mathbf U_t^{(0)}\mathbf x^{(g)}[n])^T\otimes\mathbf U_r^{(0)}$。括号内是矩阵乘法，括号外才是 Kronecker 积。</p>
<p>按原文报告的维度，元素数 $E=N_t M_t(q_{az}q_{el})^2$。若两种角度都取 $q$ 个点，则随 $q^4$ 增长，是四次多项式。</p>
<div class="repair-lab"><h3>教学计算：改变候选点与存储精度</h3>
<p class="repair-note">取 $N_t=32,M_t=20$（原文 Figure 2 的示例设置），只算单次矩阵的元素存储，不含求解器、中间量或系统开销。不是设备内存诊断。</p>
<div class="repair-controls"><label for="memory-q">每个角度的候选点 q<input id="memory-q" type="range" min="4" max="30" step="1" value="10"></label><label for="memory-bytes">每个复数元素<select id="memory-bytes"><option value="16">16 字节（complex128）</option><option value="8">8 字节（complex64）</option></select></label><button id="memory-reset" type="button">复位</button></div>
<svg class="repair-chart" viewBox="0 0 600 180" aria-label="在固定最大候选点30的比例尺上，列数与存储量的变化"><text x="10" y="30">矩阵列数（q⁴；零基线）</text><rect id="memory-bar" x="10" y="55" width="0" height="40" fill="#265976"/><text x="10" y="140" id="memory-caption"></text></svg>
<div class="repair-readout"><div>q<output id="memory-q-value"></output></div><div>列数 q⁴<output id="memory-columns"></output></div><div>元素数 E<output id="memory-elements"></output></div><div>元素存储<output id="memory-size"></output></div></div>
<p class="repair-note">论文在其模拟设置下指出，标准方法超过18个候选点时，内存和耗时变得不实用；这不是所有设备共有的溢出阈值。多次迭代累计处理的元素数也不等于峰值内存。</p></div>
'''+source_buttons(['S092','S100','S101','S193'])+'</section>',r'''
(()=>{const q=document.getElementById('memory-q'),bytes=document.getElementById('memory-bytes');
function render(){const n=Number(q.value),cols=n**4,elements=32*20*cols,size=elements*Number(bytes.value);for(const [id,v] of [['memory-q-value',n],['memory-columns',cols],['memory-elements',elements],['memory-size',size]]){const el=document.getElementById(id);el.dataset.value=String(v);el.textContent=id==='memory-size'?(size/1024**2).toFixed(2)+' MiB':v.toLocaleString('en-US');}document.getElementById('memory-bar').setAttribute('width',String(560*cols/30**4));document.getElementById('memory-caption').textContent='当前 '+cols.toLocaleString('en-US')+' 列；比例尺上限 '+(30**4).toLocaleString('en-US')+' 列';}
q.addEventListener('input',render);bytes.addEventListener('change',render);document.getElementById('memory-reset').addEventListener('click',()=>{q.value='10';bytes.value='16';render();});render();})();
''', ['复数存储精度为可选教学假设；估算不含额外开销。'])
    replace(folder,'chap-4-mechanism',r'''
<section id="adaptive-mechanism" data-node="adaptive-mechanism"><h2>自适应搜索：把网格集中到相邻候选点之间</h2>
<p>每轮先用当前感知矩阵估计最优索引，再以它左右相邻的候选角度作为下一轮区间，在局部重新均匀采样。矩阵保持较小，但局部间隔会缩小。</p>
<p>对于内部索引，原文式 (17) 使用上一轮的 $\tilde\phi_{\iota-1}^{(k-1)}$ 与 $\tilde\phi_{\iota+1}^{(k-1)}$ 作为新边界；并据式 (21)–(23) 重建矩阵。</p>
<div class="repair-lab"><h3>一维教学演示：实际重算每轮邻域</h3><p class="repair-note">用已知教学目标的最近网格点代替论文式 (8) 的多子载波最大相关搜索，仅演示内部索引的区间更新，不是论文信道估计复现。原文边界分支使用 q 符号，上下文存在歧义，本演示不据此推断边界处理。</p>
<div class="repair-controls"><label for="search-target">教学目标角度<input id="search-target" type="range" min="80" max="280" step="1" value="240"></label><button id="search-prev" type="button">上一步</button><button id="search-next" type="button">下一轮</button><button id="search-reset" type="button">复位</button></div>
<svg viewBox="0 0 600 190" class="repair-chart" aria-label="固定0至360度坐标下的搜索区间、六个候选点和教学目标"><line x1="30" y1="130" x2="570" y2="130" stroke="#596877"/><rect id="search-range" x="30" y="55" width="540" height="60" fill="#edf2f1"/><g id="search-candidates"></g><line id="search-truth" x1="390" y1="35" x2="390" y2="150" stroke="#ad472d" stroke-width="3"/><text x="30" y="175">0°</text><text x="530" y="175">360°</text></svg>
<div class="repair-readout"><div>当前轮<output id="search-iteration"></output></div><div>区间宽度（度）<output id="search-width"></output></div><div>六个候选角（度）<output id="search-values" style="font-size:14px"></output></div></div>
<p>真实算法仍受噪声、初始估计和残差更新影响。局部收缩不能保证真实目标永远在区间内，不能把教学目标的收敛当成论文实验结果。</p></div>
'''+source_buttons(['S165','S168','S192'])+'</section>',r'''
(()=>{const target=document.getElementById('search-target');let history=[[0,360]],i=0;const ns='http://www.w3.org/2000/svg';
function state(){const [lo,hi]=history[i],points=Array.from({length:6},(_,j)=>lo+j*(hi-lo)/5);let best=0;points.forEach((v,j)=>{if(Math.abs(v-Number(target.value))<Math.abs(points[best]-Number(target.value)))best=j;});return {lo,hi,points,best};}
function render(){const s=state(),x=v=>30+v/360*540;const rect=document.getElementById('search-range');rect.setAttribute('x',x(s.lo));rect.setAttribute('width',Math.max(0,x(s.hi)-x(s.lo)));const group=document.getElementById('search-candidates');group.replaceChildren();s.points.forEach((v,j)=>{const dot=document.createElementNS(ns,'circle');dot.setAttribute('cx',x(v));dot.setAttribute('cy',85);dot.setAttribute('r',j===s.best?7:4);dot.setAttribute('fill',j===s.best?'#ad472d':'#265976');group.append(dot);});const truth=document.getElementById('search-truth');truth.setAttribute('x1',x(Number(target.value)));truth.setAttribute('x2',x(Number(target.value)));for(const [id,value] of [['search-iteration',i],['search-width',s.hi-s.lo]]){const el=document.getElementById(id);el.dataset.value=String(value);el.textContent=Number(value.toFixed(6));}const values=document.getElementById('search-values');values.dataset.values=JSON.stringify(s.points);values.textContent=s.points.map(v=>v.toFixed(3)).join(', ');document.getElementById('search-prev').disabled=i===0;document.getElementById('search-next').disabled=i>=8||s.best===0||s.best===5;}
target.addEventListener('input',()=>{history=[[0,360]];i=0;render();});document.getElementById('search-next').addEventListener('click',()=>{const s=state();if(i>=8||s.best===0||s.best===5)return;history=history.slice(0,i+1);history.push([s.points[s.best-1],s.points[s.best+1]]);i++;render();});document.getElementById('search-prev').addEventListener('click',()=>{i=Math.max(0,i-1);render();});document.getElementById('search-reset').addEventListener('click',()=>{target.value='240';history=[[0,360]];i=0;render();});render();})();
''', ['六点一维教学网格，最近点代替相关搜索；仅使用内部索引分支。'])
    replace(folder,'chap-6-results',r'''
<section id="complexity-analysis" data-node="complexity-analysis"><h2>效率：比较论文真实报告的同一组实验</h2>
<p>Table 3 给出估计两条路径、全部五个参数的总执行时间与运算量。自适应法用14轮、6×6候选网格，标准法为18×18网格。耗时取决于这些实验设置，不等于任意设备的固定加速比。</p>
<div class="repair-controls"><label for="efficiency-metric">比较指标<select id="efficiency-metric"><option value="Time (s)">执行时间（秒）</option><option value="Number of Mathematical Operations">数学运算次数</option></select></label></div><div id="efficiency-bars"></div><output id="efficiency-values"></output>
'''+source_buttons(['S271','S275','S276'])+r'''</section>
<section id="simulation-results" data-node="simulation-results"><h2>精度：逐参数查看真实 RMSE</h2><p>Table 4 的 RMSE 来自100次运行，并对所有路径平均。单位随参数变化，角度用rad，到达时间用μs；不能把它们取一个混合均值。</p><div class="repair-controls"><label for="rmse-parameter">选择参数<select id="rmse-parameter"></select></label><button id="results-reset" type="button">复位</button></div><div id="rmse-bars"></div><output id="rmse-values"></output>
<p class="repair-note">这里只呈现真实表格点值。原文 Figure 4–6 有收敛曲线，但没有逐迭代数值表，本页不生成随机曲线冒充原图。</p><table><thead id="rmse-head"></thead><tbody id="rmse-rows"></tbody></table>
'''+source_buttons(['S284'])+'</section>',r'''
(()=>{const tables=window.paperMindData.tables,t3=tables.find(t=>t.id==='p11-Table_3'),t4=tables.find(t=>t.id==='p11-Table_4');if(!t3||!t4)throw Error('缺少原表3或4');
const number=s=>{if(s==null||s==='')return null;const supers={'⁰':'0','¹':'1','²':'2','³':'3','⁴':'4','⁵':'5','⁶':'6','⁷':'7','⁸':'8','⁹':'9','⁻':'-'};const clean=String(s).replace(/[⁰¹²³⁴⁵⁶⁷⁸⁹⁻]/g,c=>supers[c]);const parts=clean.match(/^([\d.]+)\s*[×x]\s*10\s*\^?\s*(-?\d+)$/);return parts?Number(parts[1])*10**Number(parts[2]):Number(clean);};
function bars(id,rows,column,output){const box=document.getElementById(id);box.replaceChildren();const values=rows.map(row=>number(row.values[column])),max=Math.max(...values.filter(v=>v!=null));rows.forEach((row,j)=>{const line=document.createElement('div');line.className='repair-bar';const label=document.createElement('span');label.textContent=row.label;const track=document.createElement('div');track.className='repair-track';const fill=document.createElement('div');fill.className='repair-fill';fill.dataset.value=String(values[j]);fill.style.width=(values[j]==null?0:100*values[j]/max)+'%';track.append(fill);const value=document.createElement('span');value.textContent=row.values[column]??'未报告';line.append(label,track,value);box.append(line);});const out=document.getElementById(output);out.dataset.values=JSON.stringify(values);out.textContent=column+'；零基线，同组最大值为比例尺上限。';}
const metric=document.getElementById('efficiency-metric'),parameter=document.getElementById('rmse-parameter');t4.columns.slice(1).forEach(c=>{const o=document.createElement('option');o.value=c;o.textContent=c;parameter.append(o);});const head=document.getElementById('rmse-head'),tr=document.createElement('tr');t4.columns.forEach(c=>{const th=document.createElement('th');th.textContent=c;tr.append(th);});head.append(tr);const tbody=document.getElementById('rmse-rows');t4.rows.forEach(row=>{const tr=document.createElement('tr');t4.columns.forEach(c=>{const td=document.createElement('td');td.textContent=row.values[c]??'未报告';tr.append(td);});tbody.append(tr);});
function render(){bars('efficiency-bars',t3.rows,metric.value,'efficiency-values');bars('rmse-bars',t4.rows,parameter.value,'rmse-values');}metric.addEventListener('change',render);parameter.addEventListener('change',render);document.getElementById('results-reset').addEventListener('click',()=>{metric.selectedIndex=0;parameter.selectedIndex=0;render();});render();})();
''')
    # Correct OCR's superscript az/el column names in the edition's cached original page.
    page=load(folder/'page-11.json')
    renames={'ε_φᶜˢ (rad)':'ε_φaz (rad)','ε_φᶜˡ (rad)':'ε_φel (rad)','ε_θᶜˢ (rad)':'ε_θaz (rad)','ε_θᶜˡ (rad)':'ε_θel (rad)'}
    for table in page['tables']:
        table['columns']=[renames.get(c,c) for c in table['columns']]
        for row in table['rows']:row['values']={renames.get(k,k):v for k,v in row['values'].items()}
    write(folder/'page-11.json',page)
    for path in (folder/'chapters').glob('*/artifact.json'):
        a=load(path)
        for field in ['html','javascript']:
            for old,new in renames.items():a[field]=a[field].replace(old,new)
        # Narrow layouts must shrink grids/plots, while wide tables scroll locally.
        a['css']+='\n@media(max-width:620px){.content-grid,.grid-layout,.interactive-stage{display:block!important}.data-row{flex-wrap:wrap}.formula-card{overflow:auto}canvas{max-width:100%;height:auto}}'
        write(path,a)
    def limits(a):
        a['javascript']=a['javascript'].replace("function drawMultiPath(ctx, x1, y1, x2, y2, color) {", "function drawMultiPath(ctx, x1, y1, x2, y2, color) {\n const h=canvas.height;")
        a['css']+='\n.viz-overlay,.viz-overlay.visible{pointer-events:none!important}'
    edit(folder,'chap-7-limits',limits)
    def algorithm(a):
        a['html']=a['html'].replace('<header', '<p class="repair-note">流程教学示意：下方能量、索引和估计值为预设状态，不是重新计算真实信道或复现论文实验。</p><header',1)
        a['css']+='\n.algo-overlay{position:static;opacity:1;background:var(--soft);color:var(--ink);pointer-events:auto}.algo-visualizer{overflow:visible}.algo-source-ref button{color:var(--accent)}@media(max-width:620px){.algo-stage{display:block!important}.algo-controls{flex-wrap:wrap}.algo-formula-card,.algo-steps-list,.algo-data-panel{padding:12px}.formula-block{overflow:auto;font-size:17px}.algo-data-panel{margin-top:20px}}'
    edit(folder,'chap-5-algo',algorithm)
    def problem(a):
        a['html']=a['html'].replace('传统 DCS-SOMP 在 3D 全参数估计中存在维度缺失和精度不足导致的流程冗长两大核心缺陷。','应区分部分相关工作的二维阵列限制，与本文标准 DCS-SOMP 基线的网格精度和效率问题。')
        a['javascript']=a['javascript'].replace("{ name: 'ToA', status: 'missing'", "{ name: 'ToA', status: 'active'")
        a['javascript']=a['javascript'].replace('传统 DCS-SOMP 在 3D 全参数估计中存在维度缺失和精度不足导致的流程冗长两大核心缺陷。','相关工作的二维限制来自各自阵列设置，不能据此说标准 DCS-SOMP 无法估计 ToA 或仰角。')
        a['html']='<p class="repair-note">本节“传统”开关概括部分二维相关工作，并非本文使用 UCA 的标准 DCS-SOMP 基线；后者也能估计五个参数。</p>'+a['html']
    edit(folder,'chap-1-problem',problem)


def rag():
    folder=r.folder(EDITIONS['rag']['edition'])
    replace(folder,'chap-1-problem',r'''
<section id="problem-statement" data-node="problem-statement"><h2>知识放在哪里，更新就发生在哪里</h2><p>纯参数模型把知识隐含在权重中，直接检查和修改特定事实很困难。RAG 将参数记忆与可替换的非参数文档索引结合，让模型能在生成时访问外部证据。</p><div class="repair-lab"><h3>结构教学：替换索引会改变哪个部分？</h3><p class="repair-note">下面是结构示意，不运行检索、训练或生成真实答案；索引变化也不保证回答正确。</p><div class="repair-controls"><label for="knowledge-version">索引版本<select id="knowledge-version"><option value="old">旧文档</option><option value="new">更新后的文档</option></select></label><button id="knowledge-reset" type="button">复位</button></div><svg viewBox="0 0 600 240" class="repair-chart" aria-label="固定参数记忆与可更换文档索引汇入生成器"><rect x="20" y="20" width="230" height="65" fill="#edf2f1"/><text x="35" y="60">参数记忆：权重保持固定</text><rect id="knowledge-index" x="20" y="140" width="230" height="65" fill="#edf2f1"/><text id="knowledge-doc" x="35" y="180">非参数记忆：旧文档</text><path id="knowledge-edge" d="M250 170 L430 120" stroke="#596877" stroke-width="3"/><path d="M250 55 L430 120" stroke="#596877" stroke-width="3"/><rect x="430" y="85" width="150" height="65" fill="#edf2f1"/><text x="445" y="125">生成器</text></svg><output id="knowledge-status"></output></div>
'''+source_buttons(['S010','S012','S036'])+'</section>',r'''
(()=>{const select=document.getElementById('knowledge-version');function render(){const updated=select.value==='new';document.getElementById('knowledge-index').setAttribute('fill',updated?'#d5e9e2':'#edf2f1');document.getElementById('knowledge-edge').setAttribute('stroke-width',updated?'6':'3');document.getElementById('knowledge-doc').textContent='非参数记忆：'+(updated?'更新后的文档':'旧文档');const out=document.getElementById('knowledge-status');out.dataset.value=updated?'new':'old';out.textContent=updated?'外部文档已替换，模型参数保持固定；输出正确性仍需检验。':'参数记忆与外部文档共同参与生成。';}select.addEventListener('change',render);document.getElementById('knowledge-reset').addEventListener('click',()=>{select.value='old';render();});render();})();
''',['索引版本仅为结构教学状态，不是真实模型更新。'])
    replace(folder,'chap-7-ablation',r'''
<section id="retrieval-ablations" data-node="retrieval-ablations"><h2>消融：在同一任务里比较检索器</h2><p>Table 6 报告开发集的单项指标。切换任务时，只比较相同指标的真实实验行，不把 QA、生成和 FEVER 的分数合并成一个平均分。</p><div class="repair-controls"><label for="ablation-task">任务与指标<select id="ablation-task"></select></label><label for="ablation-variant">生成变体<select id="ablation-variant"><option value="Token">RAG-Token</option><option value="Sequence">RAG-Sequence</option></select></label><button id="ablation-reset" type="button">复位</button></div><div id="ablation-bars"></div><output id="ablation-values"></output><p id="ablation-note" class="repair-note"></p>
<p>FEVER 是单 token 分类，两种 RAG 变体等价；原表把每种检索配置的 FEVER 分数合并展示。缺失或合并单元格不按0分计算。可学习检索器并非所有任务都最佳，须看具体任务。</p>
'''+source_buttons(['S134','S154','S156'])+'</section>',r'''
(()=>{const table=window.paperMindData.tables.find(t=>t.id==='p8-Table_6');if(!table)throw Error('缺少原表6');const task=document.getElementById('ablation-task'),variant=document.getElementById('ablation-variant');table.columns.filter(c=>c!=='Model').forEach(c=>{const o=document.createElement('option');o.value=c;o.textContent=c;task.append(o);});
function render(){const metric=task.value,kind=variant.value,fever=metric.startsWith('FVR-');variant.disabled=fever;const rows=['BM25','Frozen','Learned'].map(name=>({name,row:table.rows.find(r=>r.label==='RAG-'+(fever?'Token':kind)+(name==='Learned'?'':'-'+name))}));const box=document.getElementById('ablation-bars');box.replaceChildren();const vals=rows.map(item=>{const v=item.row?.values[metric];return v==null||v===''?null:Number(v);});rows.forEach((item,i)=>{const line=document.createElement('div');line.className='repair-bar';const label=document.createElement('span');label.textContent=item.name;const track=document.createElement('div');track.className='repair-track';const bar=document.createElement('div');bar.className='repair-fill';bar.style.width=(vals[i]??0)+'%';bar.dataset.value=vals[i]==null?'missing':String(vals[i]);track.append(bar);const value=document.createElement('span');value.textContent=vals[i]==null?'未报告':String(vals[i]);line.append(label,track,value);box.append(line);});const out=document.getElementById('ablation-values');out.dataset.values=JSON.stringify(vals);out.textContent=metric+'（开发集；0—100比例尺）';document.getElementById('ablation-note').textContent=fever?'使用原表合并的FEVER配置分数，不补造另一变体实验。':'当前只显示 '+kind+' 的同一任务结果。';}
task.addEventListener('change',render);variant.addEventListener('change',render);document.getElementById('ablation-reset').addEventListener('click',()=>{task.selectedIndex=0;variant.value='Token';render();});render();})();
''')
    def training(a):
        a['javascript']=a['javascript'].replace('除非有极强的领域适应需求，否则保持冻结是更优选择。','原文采用冻结策略并取得报告结果；未提供更新文档编码器的同条件对照，本演示不推断哪种策略普遍更优。')
    edit(folder,'chap-4-training',training)
    def generation(a):
        a['javascript']=a['javascript'].replace('SOTA Gap: ${(sotAVal - ragVal).toFixed(1)}%','SOTA差距：${(sotAVal - ragVal).toFixed(1)} 个百分点')
        a['javascript']=a['javascript'].replace('差距仅为 4.3%','准确率差距为4.3个百分点').replace('差距仅为 2.7%','准确率差距为2.7个百分点')
        a['html']='<p class="repair-note">事实性/特异性：Jeopardy人工成对评估的判定占比；多样性：不同三元组占全部三元组的比例。FEVER差值用百分点，不是相对增幅。</p>'+a['html']
    edit(folder,'chap-6-generation',generation)
    def limits(a):
        a['html']='<p class="repair-note">以下文档激活和条形高度仅为结构示意，非模型注意力权重或梯度实测。检索坍缩是论文在所述故事生成任务中观察到的现象，不代表所有低事实需求任务必然坍缩。</p>'+a['html']
        a['javascript']=a['javascript'].replace("flowLabel: '梯度更新有效'","flowLabel: '检索内容参与生成（示意）'").replace("flowLabel: '梯度消失/无效'","flowLabel: '检索未被有效利用（示意）'")
        a['javascript']=a['javascript'].replace('const rowsToShow = table7Data.rows.slice(0, 5);','const rowsToShow = table7Data.rows;')
    edit(folder,'chap-9-limits',limits)
    def architecture(a):
        a['html']='<p class="repair-note">结构教学：K 改变文档框数量，步骤按钮改变当前信息流。不执行真实检索、训练或答案生成。</p>'+a['html']
        a['javascript']=r'''
(()=>{const slider=document.getElementById('k-slider'),query=document.getElementById('query-input'),run=document.getElementById('run-simulation'),reset=document.getElementById('reset-simulation'),docs=document.getElementById('doc-highlights');let phase=3;
function render(){const k=Number(slider.value);document.getElementById('k-value').textContent=k;run.textContent='下一步：'+(['','检索','融合','输出'][phase%3+1]);for(const [id,on] of [['path-retrieve',phase>=1],['path-retrieve-up',phase>=1],['path-retrieve-down',phase>=1],['path-fuse',phase>=2],['path-generate',phase>=3]])document.getElementById(id).setAttribute('opacity',on?'1':'0.15');docs.replaceChildren();for(let i=0;i<k;i++){const rect=document.createElementNS('http://www.w3.org/2000/svg','rect');rect.setAttribute('x',210);rect.setAttribute('y',45+i*180/k);rect.setAttribute('width',100);rect.setAttribute('height',Math.max(3,160/k));rect.setAttribute('fill','#265976');rect.setAttribute('opacity',phase>=1?'0.7':'0.15');docs.append(rect);}document.getElementById('node-output').setAttribute('opacity',phase>=3?'1':'0.15');document.getElementById('text-output').textContent='y（示意）';document.getElementById('status-log').textContent='结构阶段 '+phase+'：'+['','查询检索 Top-K 文档','文档与查询作为生成依据','形成输出，仍需验证正确性'][phase]+'；K='+k+'；示例查询：'+query.value;document.querySelectorAll('.step').forEach((e,i)=>e.classList.toggle('active',i+1===phase));}
slider.addEventListener('input',render);query.addEventListener('input',render);run.addEventListener('click',()=>{phase=phase%3+1;render();});reset.addEventListener('click',()=>{phase=3;slider.value='5';query.value='Define "middle ear"';render();});render();})();
'''
    edit(folder,'chap-2-architecture',architecture)


if __name__=='__main__':
    for item in EDITIONS.values():
        target=r.folder(item['edition']);parent=r.folder(item['old'])
        shutil.copytree(parent/'chapters',target/'chapters',dirs_exist_ok=True)
        for path in parent.glob('page-*.json'):shutil.copy2(path,target/path.name)
    sensors();rag()
    for key,item in EDITIONS.items():
        result=r.generate(item['edition']);print(key,result['status'],flush=True)
