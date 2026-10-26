"""Concentrated, audited repairs after Attention's complete first chapter batch."""
import json,re,sys,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from backend import reading_v2 as r,store
eid=sys.argv[1];f=r.folder(eid);backup=f/'chapter-first-frozen';backup.mkdir(exist_ok=True)
for p in ['artifact.json','data.json','plan.json','candidate.html']:
    if not (backup/p).exists():shutil.copyfile(f/p,backup/p)
for p in (f/'chapters').glob('*/artifact.json'):
    dest=backup/'chapters'/p.parent.name;dest.mkdir(parents=True,exist_ok=True)
    if not (dest/'artifact.json').exists():shutil.copyfile(p,dest/'artifact.json')

def load(name):return json.loads((f/'chapters'/name/'artifact.json').read_text(encoding='utf-8'))
def save(name,a):(f/'chapters'/name/'artifact.json').write_text(store.encode(a),encoding='utf-8')

# Preserve the true sin/cos pairing and map pointer coordinates through canvas scale.
a=load('positional-encoding')
a['javascript']=a['javascript'].replace('const exponent = dim / d_model;','const exponent = 2 * i / d_model;')
a['javascript']=a['javascript'].replace('const x = e.clientX - rect.left;','const x = (e.clientX - rect.left) * heatmapCanvas.width / rect.width;').replace('const y = e.clientY - rect.top;','const y = (e.clientY - rect.top) * heatmapCanvas.height / rect.height;')
a['javascript']=a['javascript'].replace('const intensity = Math.floor((val + 1) / 2 * 255);\n        ctxHeat.fillStyle = `rgb(${255 - intensity}, ${intensity}, ${200})`;','const t=Math.abs(val); const from=[247,246,240],to=val>=0?[38,89,118]:[173,71,45];ctxHeat.fillStyle=`rgb(${from.map((v,i)=>Math.round(v+(to[i]-v)*t)).join(",")})`;')
a['html']=a['html'].replace('<canvas id="pe-canvas"','<p class="pe-axis-note">横轴：位置 0 → 99 · 纵轴：维度 0 → 63<br>蓝色为正、赭红为负、浅色接近 0。点击色块选择位置与维度。</p><canvas id="pe-canvas"')
a['html']=a['html'].replace('<canvas id="pe-waveform-canvas"','<p class="pe-axis-note">下图展开选中维度的编码曲线：横轴为位置，纵轴范围 −1 到 1；竖线对应当前选中位置。</p><canvas id="pe-waveform-canvas"')
a['css']+='\n.pe-axis-note{font-size:13px;line-height:1.8;color:var(--muted)}.pm-content-grid{grid-template-columns:minmax(0,1fr)}.pm-visual-workbench{max-width:100%}.pm-visual-workbench canvas{max-height:260px}.pm-control-group{flex-wrap:wrap}.pm-control-group label{min-width:0;flex-basis:180px}\n'
save('positional-encoding',a)

# Bind verification to real visible outputs and give each bar an observable identity.
a=load('complexity-analysis')
a['html']=a['html'].replace('id="complexity-visual"','id="complexity-values"').replace('id="bar-sa"','id="bar-sa" data-complexity-index="0"').replace('id="bar-rnn"','id="bar-rnn" data-complexity-index="1"').replace('id="bar-3x"','id="bar-3x" data-complexity-index="2"')
a['javascript']=a['javascript'].replace("getElementById('complexity-visual')","getElementById('complexity-values')")
a['css']=a['css'].replace('#complexity-visual','#complexity-values')
a['javascript']=a['javascript'].replace('O(${n})','${n}（随 n 线性增长）')
# Render relative lengths and readable values in independent rows; labels cannot cover bars.
start=a['javascript'].index('    const svgHeight = 150;');end=a['javascript'].index('    // 更新顺序操作提示',start)
a['javascript']=a['javascript'][:start]+'''    visualContainer.replaceChildren();
    ['自注意力 · n²d','循环层 · nd²','卷积示例 · 3nd²'].forEach((name,i)=>{
      const row=document.createElement('div');row.className='complexity-row';
      const label=document.createElement('span');label.textContent=name;
      const track=document.createElement('div');track.className='complexity-track';
      const bar=document.createElement('div');bar.dataset.complexityIndex=i;bar.style.width=(values[i]/maxVal*100)+'%';bar.className='complexity-bar complexity-'+i;track.append(bar);
      const value=document.createElement('output');value.textContent=values[i].toLocaleString();row.append(label,track,value);visualContainer.append(row);
    });
''' + a['javascript'][end:]
a['css']+='\n#complexity-values{height:auto;background:transparent}.complexity-row{display:grid;grid-template-columns:1fr;gap:5px;margin:18px 0;font-size:14px}.complexity-track{height:18px;background:#edf0ed}.complexity-bar{height:18px;background:#265976}.complexity-1{background:#ad472d}.complexity-2{background:#657862}.complexity-row output{font-variant-numeric:tabular-nums}.interaction-panel{box-shadow:none}.sequential-ops{flex-wrap:wrap;gap:12px}\n'
save('complexity-analysis',a)

# Show every reported BLEU row with a genuine number-to-length mapping.
a=load('mt-results');j=a['javascript']
start=j.index('    const models = [');end=j.index('    let maxVal',start)
j=j[:start]+'''    const models = table.rows.map(row=>({id:row.id,label:row.label,warning:row.label.includes('Transformer')&&task==='enfr'}));
''' + j[end:]
start=j.index('    // 英法任务特殊处理');end=j.index('    const scaleFactor',start)
j=j[:start]+j[end:]
start=j.index('    const scaleFactor');end=j.index('    legend.textContent',start)
j=j[:start]+'''    dataPoints.forEach(dp=>{
      const row=document.createElement('div');row.className='bleu-comparison-row';
      const name=document.createElement('span');name.textContent=dp.label;name.className='bleu-model-name';
      const track=document.createElement('div');track.className='bleu-track';
      const bar=document.createElement('div');bar.className='bleu-bar';bar.dataset.bleu=dp.value;bar.dataset.model=dp.label;bar.style.width=(dp.value/maxVal*100)+'%';if(dp.label.includes('Transformer'))bar.style.background='#ad472d';track.append(bar);
      const value=document.createElement('output');value.textContent=dp.value;row.append(name,track,value);container.append(row);
    });
''' + j[end:]
j=j.replace("legend.textContent = '数据源自 Table 2 (p8-Table_2)。英法任务高亮显示正文与表格差异。';","legend.textContent = task==='enfr'?'同一测试集 newstest2014 · 柱长从0开始。此图按原表41.8绘制；正文另写41.0，原文未解释差异，不推测原因。':'WMT 2014 · newstest2014 · BLEU越高越好。未报告的语言任务不补零；柱长从0开始。';")
start=j.index('  function renderCostChart()');end=j.index('  // 初始化',start)
j=j[:start]+'''  function renderCostChart(){
    const table=getTableData(),container=document.querySelector('#cost-chart .chart-bars'),ratio=document.getElementById('cost-ratio-output');if(!table||!container)return;
    container.replaceChildren();
    const t=document.createElement('table');t.innerHTML='<thead><tr><th>模型</th><th>EN-DE成本</th><th>EN-FR成本</th><th>原表合并列</th></tr></thead>';const b=document.createElement('tbody');
    for(const row of table.rows){if(!['row_5','row_7','row_10'].includes(row.id))continue;const tr=document.createElement('tr');for(const value of [row.label,row.values['Cost EN-DE FLOPs'],row.values['Cost EN-FR FLOPs'],row.values['Merged cost FLOPs']]){const td=document.createElement('td');td.textContent=value||'未分别列出';tr.append(td);}b.append(tr);}t.append(b);container.append(t);
    if(ratio)ratio.textContent='单位为原文估计训练 FLOPs。Transformer 的成本在原表跨语言合并单元格中列出；本页保留该口径，不据此推算精确的同语种降幅。原文“低于四分之一”的说法可回查正文。';
  }
''' + j[end:]
a['javascript']=j
a['css']+='\n.content-grid{grid-template-columns:minmax(0,1fr)}.chart-bars{height:auto;display:block;padding:0;border:0}.bleu-comparison-row{display:grid;grid-template-columns:160px minmax(0,1fr) 46px;gap:12px;align-items:center;margin:15px 0;font-size:13px}.bleu-track{height:18px;background:#edf0ed}.bleu-bar{height:18px;background:#265976}.bleu-comparison-row output{font-variant-numeric:tabular-nums;text-align:right}.chart-container{min-height:0;padding:22px 0;border:0;background:transparent}.chart-note{font-size:13px}#cost-chart{overflow-x:auto}#cost-chart table{min-width:540px}.section-heading{border-left:0;padding-left:0}@media(max-width:480px){.bleu-comparison-row{grid-template-columns:110px minmax(0,1fr) 40px;gap:8px}.bleu-model-name{font-size:12px;overflow-wrap:anywhere}}\n'
save('mt-results',a)

# Only describe the selected reported experiment; training steps are not more data.
a=load('ablation-and-generalization')
a['html']=a['html'].replace('class="pm-metric-cards"','class="pm-metric-cards" id="ablation-result"')
a['html']=a['html'].replace('深层网络 (d_model=1024)','更宽表示 (d_model=1024)')
a['html']=a['html'].replace('在小数据下优于 RNN。','在该实验中优于所列 RNN seq2seq 基线，但不是所有解析器。')
a['html']=a['html'].replace('沿用翻译模型参数即获 SOTA 级结果。','只进行了少量任务相关调参；半监督 F1 为92.7，低于表中多任务93.0和生成式RNNG的93.3，不能解读为全面最优。')
a['javascript']=a['javascript'].replace("analysisEl.textContent = text;",'''analysisEl.textContent = '原文报告行：'+row.label+'。BLEU(dev)='+bleu.toFixed(1)+'，PPL(dev)='+ppl.toFixed(2)+'；相对base的BLEU变化为'+(bleu-baseBLEU).toFixed(1)+'。仅适用于英德 newstest2013 开发集，不能据此预测任意联合配置，也不等同于newstest2014测试集结果。';
    document.getElementById('ablation-result').setAttribute('data-values',JSON.stringify([bleu,ppl]));''')
a['css']+='\n.pm-workbench{grid-template-columns:minmax(0,1fr);box-shadow:none}.pm-metric-cards{display:flex;flex-wrap:wrap;gap:24px}.pm-card{background:transparent;border:0;padding:6px 0;text-align:left;min-width:100px}.pm-chart-container{height:auto}.pm-chart-container canvas{width:100%;height:auto}.pm-comparison-grid{grid-template-columns:minmax(0,1fr)}.pm-analysis-text{border-left:0;padding:16px 0}.pm-chapter-section{border-left:0;padding-left:0}.pm-select{max-width:100%}\n'
save('ablation-and-generalization',a)

# Improve manipulation and expose all intermediate steps; zero weights render as zero.
a=load('attention-mechanisms')
for i in range(3):
    a['html']=a['html'].replace(f'type="number" id="attn-q-{i}"',f'type="range" id="attn-q-{i}"')
a['html']=a['html'].replace('值向量 V (dim=3)','V：三个位置的标量值')
a['html']=a['html'].replace('<div class="pm-lab-output">','<div id="attn-calculation" class="attn-calculation" aria-live="polite"></div><div class="pm-lab-output">')
a['javascript']=a['javascript'].replace('Math.max(2, weights[idx] * 140)','weights[idx] * 140')
a['javascript']=a['javascript'].replace('    // Update Visuals','''    const calculation=document.getElementById('attn-calculation');if(calculation){calculation.replaceChildren();
      for(const [label,values] of [['Q · K',scores],['除以 √3',scores.map(s=>s/scale)],['Softmax 权重',weights]]){const p=document.createElement('p');p.textContent=label+' → ['+values.map(v=>v.toFixed(3)).join(', ')+']';calculation.append(p);}
      const p=document.createElement('p');p.textContent='Q = ['+q.join(', ')+']；输出 = Σ(权重 × V) = '+output.toFixed(4);calculation.append(p);
    }
    // Update Visuals''')
a['html']=re.sub(r'<div class="pm-head-visual">.*?<p class="pm-limitation-note">', '''<div class="pm-head-visual">
<label for="head-select">比较两个一维投影的关注结果</label><select id="head-select"><option value="0">Head 1 · 取第一个分量</option><option value="1">Head 2 · 取第三个分量</option></select>
<p>教学设置：Head 1 的 Q/K 投影为 e₁，Head 2 为 e₃；每头 dₖ=1，V 沿用上方标量。输出投影 Wᴼ=[0.5,0.5]ᵀ。两组投影均未训练。</p>
<div id="head-weights" class="head-weight-chart" data-values="[]"></div><p id="head-concat"></p><p id="head-output" data-value="0"></p></div>
<p class="pm-limitation-note">''',a['html'],flags=re.S)
a['javascript']=a['javascript'].replace('    // Update Visuals','    updateHeads(q,k,v);\n    // Update Visuals')
a['javascript']=a['javascript'].replace('  const resetAttention =', '''  function updateHeads(q,k,v){
    const results=[0,2].map(index=>{const scores=k.map(key=>q[index]*key[index]);if(document.getElementById('attn-mask').checked)scores[2]=-1e9;const w=softmax(scores);return {w,out:w.reduce((s,value,i)=>s+value*v[i],0)};});
    const select=document.getElementById('head-select'),plot=document.getElementById('head-weights');if(!plot)return;
    const chosen=results[Number(select.value)||0];plot.dataset.values=JSON.stringify(chosen.w);plot.replaceChildren();
    chosen.w.forEach((w,i)=>{const row=document.createElement('div');row.className='head-weight-row';const label=document.createElement('span');label.textContent='位置 '+(i+1);const track=document.createElement('div');track.className='head-track';const bar=document.createElement('div');bar.className='head-bar';bar.style.width=w*100+'%';track.append(bar);const value=document.createElement('output');value.textContent=w.toFixed(3);row.append(label,track,value);plot.append(row);});
    document.getElementById('head-concat').textContent='拼接输出 ['+results.map(r=>r.out.toFixed(3)).join(', ')+']';
    const output=results.reduce((s,r)=>s+r.out,0)/2;const el=document.getElementById('head-output');el.dataset.value=output;el.textContent='经 Wᴼ 投影后的示例输出：'+output.toFixed(4);
  }
  document.getElementById('head-select').addEventListener('change',calculateAttention);
  const resetAttention =''')
a['css']+='\n.head-weight-row{display:grid;grid-template-columns:55px minmax(0,1fr) 50px;gap:12px;align-items:center;margin:12px 0;font-size:14px}.head-track,.head-bar{height:18px}.head-track{background:#edf0ed}.head-bar{background:#ad472d}#head-select{margin:14px 0;max-width:100%}\n'
a['css']+='\n.pm-content-grid{grid-template-columns:minmax(0,1fr)}.pm-text-flow{line-height:1.9}.pm-lab-panel{display:block;padding:24px;background:#fff}.pm-input-row input[type=range]{min-width:0;flex:1;width:0}.pm-input-row{align-items:center}.pm-bars-container{margin-top:28px}.attn-calculation{font-size:14px;line-height:1.9;font-variant-numeric:tabular-nums;padding-top:12px;border-top:1px solid var(--line)}.attn-calculation p{margin:8px 0}.pm-bar{min-height:0}.pm-bar-val{font-size:12px}.pm-output-row{gap:16px}.pm-input-row input,.pm-matrix-grid input{min-width:0}.pm-head-visual{display:block}\n'
save('attention-mechanisms',a)

# Apply a consistent reading surface without constraining the document's graphics.
for p in (f/'chapters').glob('*/artifact.json'):
    a=json.loads(p.read_text(encoding='utf-8'))
    a['css']+='''
section[id]{--ink:#233342;--muted:#596877;--accent:#265976;--warm:#ad472d;--line:#d6dcd9;--paper:#fcfbf8;background:transparent;border:0;border-radius:0;padding:0;max-width:100%;color:var(--ink)}
section[id] h2{color:#233342;font-family:Georgia,"Noto Serif SC",SimSun,serif;font-weight:500;font-size:29px;line-height:1.5}
section[id]>header{border-bottom:1px solid #d6dcd9}section[id] p{line-height:1.9}
section[id] [class*="formula"]{max-width:100%;overflow-x:auto}
section[id] [class*="panel"],section[id] [class*="workbench"]{box-shadow:none}
@media(max-width:600px){section[id] div{min-width:0;max-width:100%}section[id] h2{font-size:25px}section[id] [class*="grid"]{grid-template-columns:minmax(0,1fr)}section[id] .pm-matrix-grid{grid-template-columns:repeat(3,minmax(0,1fr))}section[id] .pm-input-row input{min-width:0;flex:1;width:0}section[id] .pm-control-group{flex-wrap:wrap}section[id] .pm-control-group label{min-width:0;flex-basis:100%}section[id] .pm-section-header{flex-wrap:wrap}section[id] .pm-lab-panel,section[id] .interaction-panel{padding:14px}section[id] .pm-head-visual{display:block}section[id] .pm-control-group span{min-width:0}}
'''
    p.write_text(store.encode(a),encoding='utf-8')

plan=json.loads((f/'plan.json').read_text(encoding='utf-8'))
plan['thesis']='让每个位置直接读取其他位置，再按相关性汇聚信息。Transformer 用注意力替代循环与卷积，在论文的机器翻译实验中取得领先结果；优势取决于任务、序列长度与比较口径。'
plan['boundaries'][1]='原文估计训练成本并报告英法任务成本低于此前最优模型的四分之一；表格中Transformer成本使用合并单元格，本讲解不把它擅自细分为各语言的精确成本。'
(f/'plan.json').write_text(store.encode(plan),encoding='utf-8')
(f/'repair-record.json').write_text(store.encode({'batch':'chapter-first','method':'Targeted code/content edits after complete browser/host/model reviews','changed':['PE paired frequency and pointer mapping','visible calculation bindings','all real BLEU rows and no unsupported cost ratios','ablation conditions and parsing exceptions','Q controls/intermediate values/zero weights','reading hierarchy/mobile layout','thesis scope'],'originals':'chapter-first-frozen'}),encoding='utf-8')
print('Concentrated repairs saved; no unrelated document was generated.')
