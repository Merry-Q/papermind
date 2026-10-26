"""Retain model objections, resolve only requirements outside the uploaded page."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend import store,reading_v2 as r
from extend_reading_v2 import OUT
from benchmark_reading_v2 import save

if __name__=='__main__':
    if not (OUT/'first-pass-complete.json').exists():raise SystemExit('Finish the additional-upload batch first.')
    did='pdf-1a02a680ff1cd6e0'
    with store.connection() as db:doc=store.get_document(db,did)
    expected=json.loads((OUT/'transformer-excerpt/canonical-after.json').read_text(encoding='utf-8'))
    assert r.document_hash(doc)==r.document_hash(expected),'Document edited since first pass; inspect before resolving.'
    assert doc['page_count']==1 and len(doc['sources'])==1
    v=doc['verification']
    assert all(i['verdict']=='supported' for i in v['items']) and not v['structure_issues']
    assert not doc['parser_summary']['gaps']
    quote=doc['sources'][0]['quote']
    assert '3.1 Encoder and Decoder Stacks' in quote and '3.2 Attention' in quote
    save(OUT/'transformer-excerpt/scope-before.json',doc)
    audit={'at':r.now(),'scope':'Uploaded single architecture page, section 3.1 and opening of 3.2.',
      'source_id':doc['sources'][0]['id'],
      'reason':'The upload ends at the weighted-sum introduction. Head count, d_ff, full scaled attention and section3.5 sinusoidal formulas are not on this uploaded page; not extraction/coverage defects.',
      'retained_source_and_nodes':True,'requires_no_fabricated_original_content':True}
    v['coverage_model_review']=v['coverage']
    v['coverage']={'verdict':'covered','gaps':[],'basis':'engineering_source_scope_recheck','audit':audit}
    doc.update(status='ready',generation_gaps=[],verification=v,revision=doc['revision']+1)
    with store.connection(write=True) as db:store.put_document(db,doc)
    save(OUT/'transformer-excerpt/scope-resolution.json',audit)
    save(OUT/'transformer-excerpt/scope-after.json',doc)
    print('Single-page scope corrected; original model objections retained; nodes/sources unchanged.')
