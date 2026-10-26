"""Inspect only finalized bytes; record exactly which edition/hash was exercised."""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend import reading_v2 as r
from extend_reading_v2 import OUT,CASES
from verify_other_materials import browser,review
from benchmark_reading_v2 import save

def read(p):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except (OSError,json.JSONDecodeError):return None

if __name__=='__main__':
    done={};reviews=[];futures={}
    with ThreadPoolExecutor(max_workers=2) as pool:
        while len(done)<len(CASES):
            for key,_,_ in CASES:
                p=OUT/key/('generation.json' if key=='adaptive-dcs-somp' else 'repair.json');v=read(p)
                if not v or v.get('status')!='draft' or (key!='adaptive-dcs-somp' and not v.get('engineering_final_at')):continue
                a=read(r.folder(v['edition'])/'artifact.json')
                if not a:continue
                signature={'edition':v['edition'],'artifact_hash':r.digest(a)}
                if done.get(key)==signature:continue
                dest=OUT/key/'acceptance';prior=read(dest/'candidate.json')
                if prior!=signature or not (dest/'report.json').exists():
                    if dest.exists():
                        old=dest.with_name('acceptance-before-'+str(time.time_ns()))
                        assert OUT.resolve() in dest.resolve().parents and OUT.resolve() in old.resolve().parents
                        dest.rename(old)
                    browser(v,'acceptance');save(dest/'candidate.json',signature)
                if key not in ['rag','adaptive-dcs-somp','macroeconomics-ai'] and not (dest/'review-summary.json').exists():futures[pool.submit(review,v,'acceptance')]=key
                done[key]=signature;save(OUT/'acceptance-candidates.json',done)
            for future in list(futures):
                if future.done():reviews.append(future.result());del futures[future];save(OUT/'acceptance-reviews.json',reviews)
            if len(done)<len(CASES):time.sleep(4)
        for future in as_completed(futures):reviews.append(future.result());save(OUT/'acceptance-reviews.json',reviews)
    save(OUT/'acceptance-complete.json',{'candidates':done,'reviews':reviews,'published':False})
