"""Compact, source-linked progress and issue ledger, with no product mutations."""
import json
from pathlib import Path
from extend_reading_v2 import OUT, CASES

def read(path):
    try:return json.loads(path.read_text(encoding='utf-8'))
    except (OSError,json.JSONDecodeError):return {}

rows=[];issues=[]
for key,did,_ in CASES:
    dest=OUT/key
    v=read(dest/'generation.json');b=read(dest/'first-pass/report.json')
    h=read(dest/'first-pass/host/report.json')
    fidelity=read(dest/'first-pass/fidelity-review.json')
    experience=read(dest/'first-pass/experience-review.json')
    row={'case':key,'document':did,'edition':v.get('edition'),'generation':v.get('status','pending'),
         'browser':b.get('status','pending'),'host':h.get('status','pending'),
         'fidelity':fidelity.get('verdict','pending'),'experience':experience.get('verdict','pending')}
    rows.append(row)
    if v.get('error'):issues.append({'case':key,'kind':'generation','detail':v['error']})
    for kind,result in [('browser',b),('host',h)]:
        for issue in result.get('issues',[]):issues.append({'case':key,'kind':kind,**issue})
    for kind,result in [('fidelity',fidelity),('experience',experience)]:
        for finding in result.get('findings',[]):issues.append({'case':key,'kind':kind,**finding})
manual=read(OUT/'manual-first-observations.json')
if isinstance(manual,list):issues.extend({'kind':'engineering',**item} for item in manual)
value={'cases':rows,'issues':issues,'first_pass_complete':(OUT/'first-pass-complete.json').exists()}
(OUT/'issue-ledger.json').write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(value,ensure_ascii=False,indent=2))
