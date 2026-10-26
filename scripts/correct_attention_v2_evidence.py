"""Audited correction for this fixed corpus PDF, not a generic extraction shortcut.
Values were checked against rendered pages 8/9 and native PDF word coordinates.
"""
import sys,json,shutil,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from backend import reading_v2 as r,store
eid=sys.argv[1];f=r.folder(eid)
with store.connection() as db:doc=store.get_document(db,r.get(eid)['document_id'])
pdf_hash=hashlib.sha256(Path(doc['file_path']).read_bytes()).hexdigest()
assert pdf_hash=='bdfaa68d8984f0dc02beaca527b76f207d99b666d31d1da728ee0728182df697'
backup=f/'vision-originals';backup.mkdir(exist_ok=True)
for page in [8,9]:
    if not (backup/f'page-{page}.json').exists():shutil.copyfile(f/f'page-{page}.json',backup/f'page-{page}.json')
p=json.loads((f/'page-8.json').read_text(encoding='utf-8'));t=p['tables'][0]
columns=['Model','BLEU EN-DE','BLEU EN-FR','Cost EN-DE FLOPs','Cost EN-FR FLOPs','Merged cost FLOPs']
raw=[
 ['ByteNet [18]','23.75',None,None,None,None],
 ['Deep-Att + PosUnk [39]',None,'39.2',None,'1.0e20',None],
 ['GNMT + RL [38]','24.6','39.92','2.3e19','1.4e20',None],
 ['ConvS2S [9]','25.16','40.46','9.6e18','1.5e20',None],
 ['MoE [32]','26.03','40.56','2.0e19','1.2e20',None],
 ['Deep-Att + PosUnk Ensemble [39]',None,'40.4',None,'8.0e20',None],
 ['GNMT + RL Ensemble [38]','26.30','41.16','1.8e20','1.1e21',None],
 ['ConvS2S Ensemble [9]','26.36','41.29','7.7e19','1.2e21',None],
 ['Transformer (base model)','27.3','38.1',None,None,'3.3e18'],
 ['Transformer (big)','28.4','41.8',None,None,'2.3e19']]
t['columns']=columns;t['rows']=[{'id':f'row_{i+1}','label':v[0],'values':dict(zip(columns,v))} for i,v in enumerate(raw)]
t['notes'].append('人工对照原页与原生文字纠正多级表头；Transformer成本位于跨语言合并单元格，保留Merged cost，不人为指定语言列。41.8为表格值，正文41.0另行保留。')
(f/'page-8.json').write_text(store.encode(p),encoding='utf-8')
p=json.loads((f/'page-9.json').read_text(encoding='utf-8'));t=p['tables'][0];rows={row['id']:row for row in t['rows']}
for i,(h,dk) in enumerate([(1,512),(4,128),(16,32),(32,16)],1):
    v=rows[f'A_{i}']['values'];v.update(d_ff=None,h=str(h),d_k=str(dk),d_v=str(dk));rows[f'A_{i}']['label']=f'(A) h={h}'
for i,dk in enumerate([16,32],1):rows[f'B_{i}']['values'].update(h=None,d_k=str(dk));rows[f'B_{i}']['label']=f'(B) d_k={dk}'
for i,d in [(4,256),(5,1024)]:rows[f'C_{i}']['values'].update(N=None,d_model=str(d));rows[f'C_{i}']['label']=f'(C) d_model={d}'
for i,d in [(6,1024),(7,4096)]:rows[f'C_{i}']['values'].update(N=None,d_ff=str(d));rows[f'C_{i}']['label']=f'(C) d_ff={d}'
for i,n in [(1,2),(2,4),(3,8)]:rows[f'C_{i}']['label']=f'(C) N={n}'
for i in [1,2]:rows[f'D_{i}']['label']=f'(D) dropout={rows[f"D_{i}"]["values"]["P_drop"]}'
for i in [3,4]:rows[f'D_{i}']['label']=f'(D) label smoothing={rows[f"D_{i}"]["values"]["ε_ls"]}'
rows['E']['label']='(E) learned positional embedding'
t['notes'].append('人工对照原 PDF 字坐标与渲染原页纠正列错位；空白字段继承base仅依据原表注释；big未列出的dk/dv不自行补算为论文报告值。')
(f/'page-9.json').write_text(store.encode(p),encoding='utf-8')
(f/'evidence-correction.json').write_text(store.encode({'pdf_sha256':pdf_hash,'pages':[8,9],'method':'Rendered originals + native PDF word coordinates, reviewed by Codex','originals':'vision-originals','changes':['Table2 unique hierarchical column keys, preserve missing and merged cells','Table3 A/B/C column alignment, descriptive row labels'],'scope':'Attention corpus case only'}),encoding='utf-8')
print('Corrected 2 evidence pages; originals preserved.')
