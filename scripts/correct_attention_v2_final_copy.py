"""Correct concrete source/semantic defects found in final rendered-content readback."""
import json,sys,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from backend import reading_v2 as r,store
f=r.folder(sys.argv[1]);r.update(f.name,status='draft',stage='final_source_corrections')
changes={
 'training-regime':{'虽然标签平滑会降低困惑度（使模型更“不确定”），但能提升准确率和 BLEU 分数。':'标签平滑让模型对预测更不确定；原文指出它会使困惑度指标变差，但能提升准确率和 BLEU 分数。'},
 'transformer-architecture':{
 '解码器的第二子层（实际上是整个解码器层的第三个子层）执行多头注意力。此时 Query 来自解码器上一层':'解码器的第二个子层执行编码器—解码器多头注意力。此时 Query 来自解码器前一子层的输出',
 '位置 i 只能关注位置 <i 的信息':'位置 i 只能关注当前位置及更早位置的信息',
 '架构参数验证':'结构示意参数（非实验预测）'},
 'mt-results':{'Transformer (big) 英法训练成本为 2.3·10¹⁹ FLOPs。作者声称这是\'此前 SOTA\'的 1/4 以下。下表对比具体比例。':'原表报告 Transformer (big) 估计训练成本为 2.3·10¹⁹ FLOPs，位于跨语言合并单元格中。下表保留原始列口径，不把该值自行细分为各语言的精确训练成本。'},
 'complexity-analysis':{'<li>O(n²) 的内存消耗在当时的硬件条件下是可接受的，或者可以通过后续优化解决。</li>':''}
}
for name,replacements in changes.items():
 p=f/'chapters'/name/'artifact.json';a=json.loads(p.read_text(encoding='utf-8'));backup=p.with_name('before-final-copy.json')
 if not backup.exists():shutil.copyfile(p,backup)
 for field in ['html','javascript']:
  for old,new in replacements.items():a[field]=a[field].replace(old,new)
 p.write_text(store.encode(a),encoding='utf-8')
(f/'final-copy-corrections.json').write_text(store.encode(changes),encoding='utf-8');print('Corrected concrete final-copy defects; original drafts preserved.')
