"""One final browser/host pass per candidate, re-review changed authored chapters."""
import json
import time
from concurrent.futures import ThreadPoolExecutor,as_completed
from extend_reading_v2 import OUT,CASES
from verify_other_materials import browser,review
from benchmark_reading_v2 import save

def read(path):
    try:return json.loads(path.read_text(encoding='utf-8'))
    except (OSError,json.JSONDecodeError):return None

if __name__=='__main__':
    done=set();results=[];futures={}
    with ThreadPoolExecutor(max_workers=2) as pool:
        while len(done)<len(CASES):
            specs=read(OUT/'repair-plan.json') or {}
            for key,_,_ in CASES:
                if key in done:continue
                record=OUT/key/('repair.json' if key in specs else 'generation.json')
                v=read(record)
                if not v or v.get('status') not in ['draft','failed']:continue
                if not (OUT/key/'final-pass/report.json').exists():browser(v,'final-pass')
                if specs.get(key,{}).get('chapters') or specs.get(key,{}).get('plan_nodes') or key in ['hyperbolic-location','transformer-excerpt','5g-overview']:
                    futures[pool.submit(review,v,'final-pass')]=key
                else:
                    save(OUT/key/'final-pass/retained-source-review.json',{
                      'source':'../first-pass/fidelity-review.json','reason':'No new factual prose; targeted code/style changes require independent numeric/visual checks.',
                      'edition':v.get('edition'),'not_a_new_model_review':True})
                done.add(key)
            for future in list(futures):
                if future.done():results.append(future.result());del futures[future];save(OUT/'final-review-summary.json',results)
            if len(done)<len(CASES):time.sleep(4)
        for future in as_completed(futures):results.append(future.result());save(OUT/'final-review-summary.json',results)
    save(OUT/'final-pass-complete.json',{'cases':sorted(done),'reviews':results,'published':False})
