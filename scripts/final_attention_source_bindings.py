import json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from backend import reading_v2 as r,store
f=r.folder(sys.argv[1]);p=f/'chapters/transformer-architecture/artifact.json';a=json.loads(p.read_text(encoding='utf-8'))
for title,refs in [('输入嵌入与编码',['S074','S036']),('解码器自注意力（带掩码）',['S037','S070']),('编码器 - 解码器注意力',['S068']),('前馈与输出生成',['S071','S074'])]:
    pattern='(title: '+re.escape(json.dumps(title,ensure_ascii=False))+r'.*?sourceIds: )\[[^\]]*\]'
    a['javascript'],count=re.subn(pattern,lambda m:m.group(1)+json.dumps(refs),a['javascript'],count=1,flags=re.S);assert count==1,title
a['javascript']=a['javascript'].replace('整个过程重复直到生成结束标记。','模型按自回归方式逐个生成后续符号。')
a['html']=a['html'].replace('当前状态数据:','当前示意配置:').replace('当前状态数据：','当前示意配置：')
a['javascript']=a['javascript'].replace('outputDisplay.textContent = JSON.stringify(data);','outputDisplay.textContent = `步骤 ${state.step+1}/${state.steps.length} · 层数 ${state.layers} · d_model=${state.dModel} · 掩码${state.maskVisible?"开启":"关闭"}`;')
p.write_text(store.encode(a),encoding='utf-8')
p=f/'chapters/training-regime/artifact.json';a=json.loads(p.read_text(encoding='utf-8'));a['html']=a['html'].replace('数据源自 window.paperMindData.tables。null 值未显示。','数据源自原文 Table 2；空缺数据不补零。');p.write_text(store.encode(a),encoding='utf-8')
print('Bound every architecture step to its exact supporting paragraph.')
