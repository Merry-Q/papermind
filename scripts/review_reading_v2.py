"""Independent source and rendered-design review for one frozen edition batch."""
import argparse,base64,json,sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from backend import reading_v2 as r,model_gateway as gateway,store
from backend.reading_v2_contracts import ReadingReview

def main():
    p=argparse.ArgumentParser();p.add_argument('--edition',required=True);p.add_argument('--batch',required=True);a=p.parse_args()
    f=r.folder(a.edition);out=Path(a.batch);out.mkdir(parents=True,exist_ok=True)
    pack=json.loads((f/'evidence.json').read_text(encoding='utf-8'));artifact=json.loads((f/'artifact.json').read_text(encoding='utf-8'));data=json.loads((f/'data.json').read_text(encoding='utf-8'))
    browser=json.loads((out/'report.json').read_text(encoding='utf-8'))
    context={'feature':r.VERSION,'reading_edition_id':a.edition,'batch':str(out)}
    def fidelity():
        evidence={'original_pages':[p for p in pack['pages'] if p['page']<=10],'sources':data['sources'],'tables':data['tables'],'artifact':artifact,'actual_operations':browser['checks']}
        review=gateway.structured('reviewer','独立核验这份交互论文讲解。必须逐章确认十个核心节点（问题、架构、缩放注意力、多头、位置、复杂度、训练、翻译结果、消融、泛化）是否有实质解释且来源支持。核查来源ID与原句是否支持主张，公式与假设、输入维度、理论量级与实际耗时、训练并行与自回归推理、开发集与测试集、所有真实实验行、教学值标识。表2英法正文41.0与表中41.8不可擅自统一。消融不能合成新实验。不要把技术测试通过直接说成学习有效。只报告有具体证据的缺陷，不能要求未在原文论证的更强保证。verdict只有没有blocker时才pass；coverage列实际覆盖的节点。',evidence,ReadingReview,max_tokens=7000,context=context)
        (out/'fidelity-review.json').write_text(store.encode(review),encoding='utf-8');return {'fidelity':review}
    def experience():
        shots=[out/n for n in ['desktop-hero.png','desktop-attention.png','desktop-position.png','desktop-evidence.png','mobile-attention.png'] if (out/n).exists()]
        content=[{'type':'text','text':'评审这份论文交互讲解的实际截图与操作摘要。判断机制操作是否帮助看见原因与结果、默认图是否建立直觉、是否存在标签遮挡/小字/无意义控件/手机溢出/图文重复。不要求测验或打分。重要缺陷写blocker，小处写minor；只有没有blocker才pass。不要把被截图裁出视口的页面其余部分当成缺失，长页本来可以滚动。输出JSON Schema:'+store.encode(ReadingReview.model_json_schema())+'。操作摘要:'+store.encode(browser['checks'])}]
        for shot in shots:content.extend([{'type':'text','text':shot.name},{'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(shot.read_bytes()).decode()}}])
        review=ReadingReview.model_validate(gateway.request('vision',[{'role':'user','content':content}],max_tokens=7000,context=context)).model_dump()
        (out/'experience-review.json').write_text(store.encode(review),encoding='utf-8');return {'experience':review}
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(fidelity),pool.submit(experience)]
        for future in futures:print(store.encode(future.result()),flush=True)

if __name__=='__main__':main()
