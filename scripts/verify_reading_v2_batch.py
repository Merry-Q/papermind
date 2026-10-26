"""Read-only first-pass cross-domain verification and durable issue ledger."""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import subprocess
import shutil
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend import reading_v2 as reading, model_gateway as gateway, store, settings
from backend.reading_v2_contracts import ReadingReview
from benchmark_reading_v2 import CASES, protected, implementation, save

CRITERIA = {
 'rag': '参数记忆与检索记忆；RAG-Sequence与RAG-Token的边缘化次序；检索器与生成器的联合训练范围；实际任务指标、检索数量与测试集；检索不保证答案正确；不得混入Transformer翻译实验。',
 'adaptive-dcs-somp': '5G毫米波大规模MIMO、TOA与二维到达/出发角、稀疏假设、迭代收缩搜索空间/感知矩阵的自适应机制；按原算法核验更新、终止和误差；仿真配置/曲线不能伪造，不将参数估计等同完整定位。',
 'shannon': '离散熵、条件熵、信息率与信道容量的定义和条件；信源编码与信道编码的区别；噪声信道与高斯连续信道的适用边界；公式和单位bit/bit每秒，不能把教学模型当成论文实测或把PDF页码当期刊页码。',
 'lyrics': '歌词语料范围和时间跨度、流行度分组、词汇/长度/重复/速度/可读性指标、词嵌入与WEAT的效应量/显著性；观察相关不支持因果或个体歧视判断；真实样本量、表头和图数据。',
 'moral-machine': '描述性偏好不等于规范伦理；情景决策数、参与者数、国家数不可混同；属性控制、AMCE含义与置信区间、国家聚类/样本自选择与代表性；不可推断应当牺牲谁。',
 'simulation-argument': '至少一个为真的三分论证、基底独立性与意识前提、后人类文明比例/模拟数量/模拟观察者比例的定义、条件概率和参照类假设；不能把论证当现实证据或编造实测概率；原文没有实证图表。',
 'generative-ai-work': '冻结arXiv v1版本：5,179名客服人员、平均每小时解决问题增加14%；工具错峰引入与识别假设、技能/经验异质性、客户与留任结果；不能混入后续5,172人版本，教学情景不等于因果实测或工资收益。',
 'macroeconomics-ai': '冻结MIT May2024作者稿；任务暴露与可自动化份额、成本节省、Hulten定理/TFP估算和10年期限、易学与难学任务、GDP与TFP及工资分配差别；按原文核验所有百分数和分母，不混入后续期刊版本；情景估算不是未来已证实结果。',
}


def diagnostic(value, dest):
    """Inspect retained raw chapters without changing their failed product edition."""
    folder=Path(value['folder'])
    if not all((folder/name).exists() for name in ['plan.json','evidence.json','data.json']): return None
    plan=json.loads((folder/'plan.json').read_text(encoding='utf-8'))
    if not all((folder/'chapters'/c['id']/'artifact.json').exists() for c in plan['chapters']): return None
    work=dest/'diagnostic-work';work.mkdir(exist_ok=True)
    shutil.copytree(folder/'chapters',work/'chapters',dirs_exist_ok=True)
    pack=json.loads((folder/'evidence.json').read_text(encoding='utf-8'))
    data=json.loads((folder/'data.json').read_text(encoding='utf-8'))
    def cache_only(path, fn):
        if not path.exists():raise ValueError('Diagnostic never requests new model content')
        return json.loads(path.read_text(encoding='utf-8'))
    from backend.reading_v2_author import compose
    artifact=compose(work,plan,pack,data,None,{},cache_only,lambda *_:None)
    save(dest/'diagnostic-artifact.json',artifact)
    html=reading.frame_html(artifact,data,reading.get(value['edition']),'diagnostic')
    path=dest/'diagnostic-unvalidated.html';path.write_text(html,encoding='utf-8')
    save(dest/'diagnostic-scope.json',{'kind':'isolated unvalidated retained-chapter diagnostic',
         'product_status':value['status'],'product_error':value.get('error'),
         'product_edition_unchanged':True,'validation_bypassed_for_diagnostics_only':True,
         'host_checks':'blocked: failed edition is correctly unavailable in product'})
    return path


def review(value, out):
    key = value['case']
    folder = Path(value['folder'])
    dest = out / key
    dest.mkdir(exist_ok=True)
    result = {'case': key, 'generation_status': value['status'], 'checks': {}}
    if not (folder / 'evidence.json').exists():
        return {**result, 'status': 'blocked', 'reason': 'no evidence pack'}
    pack = json.loads((folder / 'evidence.json').read_text(encoding='utf-8'))
    candidate = folder / 'artifact.json'
    chapters = list(folder.glob('chapters/*/artifact.json'))
    if not candidate.exists() and not chapters:
        save(dest / 'review.json', {**result, 'status': 'blocked', 'reason': 'generation failed before authored content'})
        return {**result, 'status': 'blocked', 'reason': 'generation failed before authored content'}
    diagnostic_artifact=dest/'diagnostic-artifact.json'
    artifact = json.loads(candidate.read_text(encoding='utf-8')) if candidate.exists() else json.loads(diagnostic_artifact.read_text(encoding='utf-8')) if diagnostic_artifact.exists() else {'partial_chapters': [json.loads(p.read_text(encoding='utf-8')) for p in chapters]}
    data = json.loads((folder / 'data.json').read_text(encoding='utf-8')) if (folder / 'data.json').exists() else {}
    browser = json.loads((dest / 'report.json').read_text(encoding='utf-8')) if (dest / 'report.json').exists() else {'status': 'blocked'}
    traces = [{k: c.get(k) for k in ['chapter', 'id', 'tag', 'type', 'label', 'traces', 'errors', 'observableChange']} for c in browser.get('controls', [])]
    evidence = {'title': pack['title'], 'acceptance_focus': CRITERIA[key], 'full_original_pages': pack['pages'],
                'canonical_sources': pack['sources'], 'canonical_nodes': pack['nodes'],
                'extracted_tables': data.get('tables', []), 'generated_artifact': artifact,
                'actual_operations': traces, 'browser_issues': browser.get('issues'), 'partial_only': not candidate.exists()}
    context = {'feature': 'reading.v2.cross-domain-review', 'reading_edition_id': value['edition'], 'case': key}
    try:
        instruction = ('独立审查冻结版本的论文交互讲解，以完整原文为最高证据。不得把生成表格或节点当作独立证据。逐章核对核心论证、公式、数据、单位、引用原句是否支持主张。'
                       '对操作轨迹中已有数值，按原文公式独立复算至少一个有意义默认/变更状态，给出具体输入、期望结果与实际结果，不能只说通过。哲学与人文优先检验逻辑关系、条件和因果边界，不强迫数字或滑块。'
                       '区分原始论文数据和明确标注的教学值；辨别误用Attention模板/无依据实验。每项缺陷须指出生成位置/代码或数值、原PDF页码/原句及矛盾。'
                       '如果只有部分章节，明确产品生成未成功，不能判整篇合格；不因为该阶段故意没合并就虚构内容错误。不要求测验、打分和原文未承诺的因果保证。'
                       '只依据可见证据给出blocker/minor。coverage写实际核对的原文节点与独立复算/关系检查结果。pass只是本次模型审阅结果，并不等于发布授权。')
        fidelity = gateway.structured('reviewer', instruction, evidence, ReadingReview, max_tokens=8500, context=context)
        save(dest / 'fidelity-review.json', fidelity)
        result['checks']['fidelity'] = fidelity
    except Exception as e:
        result['checks']['fidelity_error'] = settings.sanitize(e)
    if (candidate.exists() or diagnostic_artifact.exists()) and browser.get('screenshots'):
        shots = [dest / p for p in browser['screenshots'] if p in ['desktop-hero.png', 'chapter-0.png', 'chapter-2.png', 'chapter-4.png', 'mobile-hero.png']]
        content = [{'type': 'text', 'text': '审查不同专业论文的完整交互讲解截图（仅为长页的局部视口）和操作结果。不要把截图未覆盖的内容当缺失。判断字号、遮挡、标签、主视觉、机制/关系是否可读、移动端是否溢出、按钮是否只有装饰反馈。不评价未见到的功能，不要求测验或评分。具体问题标blocker或minor，给出截图名和可见证据。JSON Schema:'+store.encode(ReadingReview.model_json_schema())+'。摘要:'+store.encode({'title':pack['title'],'chapters':browser.get('chapters'),'issues':browser.get('issues')})}]
        for shot in shots:
            content.extend([{'type':'text','text':shot.name},{'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(shot.read_bytes()).decode()}}])
        try:
            experience = ReadingReview.model_validate(gateway.request('vision',[{'role':'user','content':content}],max_tokens=5500,context=context)).model_dump()
            save(dest / 'experience-review.json', experience)
            result['checks']['experience'] = experience
        except Exception as e:
            result['checks']['experience_error'] = settings.sanitize(e)
    result['status'] = 'reviewed_no_promotion'
    save(dest / 'review.json', result)
    print('REVIEW END', key, result['checks'].get('fidelity',{}).get('verdict',result['checks'].get('fidelity_error')), flush=True)
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--batch',required=True);a=p.parse_args()
    out=store.ROOT/'artifacts/reading-v2'/a.batch
    browser_done=set()
    while True:
        for key in CASES:
            record=out/(key+'.json')
            if key in browser_done or not record.exists(): continue
            try: value=json.loads(record.read_text(encoding='utf-8'))
            except json.JSONDecodeError: continue
            if value['status']=='running': continue
            dest=out/key;dest.mkdir(exist_ok=True)
            diagnostic_path=None
            if value['status']!='draft':
                save(dest/'browser-blocked.json',{'reason':'generation failed; no complete product candidate','error':value.get('error')})
                try:diagnostic_path=diagnostic(value,dest)
                except Exception as error:save(dest/'diagnostic-error.json',{'detail':str(error)})
            if value['status']=='draft' or diagnostic_path:
                print('BROWSER START',key,flush=True)
                try:
                    command=['node','scripts/validate-reading-v2-generic.mjs',str(diagnostic_path or Path(value['folder'])/'candidate.html'),str(dest)]
                    if value['status']=='draft':command.append(value['preview_url'])
                    proc=subprocess.run(command,cwd=store.ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=600)
                    (dest/'browser-stdout.txt').write_text(proc.stdout,encoding='utf-8')
                    (dest/'browser-stderr.txt').write_text(proc.stderr,encoding='utf-8')
                    if proc.returncode: save(dest/'browser-infrastructure-error.json',{'returncode':proc.returncode,'detail':proc.stderr[-2000:]})
                except Exception as error: save(dest/'browser-infrastructure-error.json',{'detail':str(error)})
                print('BROWSER END',key,flush=True)
            browser_done.add(key)
        summary=out/'generation-summary.json'
        if summary.exists():
            try: finished=json.loads(summary.read_text(encoding='utf-8')).get('all_cases_finished')
            except json.JSONDecodeError: finished=False
            if finished and len(browser_done)==8: break
        time.sleep(8)
    # Model reviews start after generation: never multiply gateway limits across processes.
    values=[json.loads((out/(key+'.json')).read_text(encoding='utf-8')) for key in CASES]
    reviews=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(review,v,out) for v in values]):
            reviews.append(future.result())
            save(out/'review-summary.json',{'finished':len(reviews),'total':8,'results':reviews})
    before=json.loads((out/'protected-before.json').read_text(encoding='utf-8'))
    after=protected();save(out/'protected-after-tests.json',after)
    frozen=json.loads((out/'implementation.json').read_text(encoding='utf-8'))
    save(out/'verification-summary.json',{'all_cases_finished':True,'finished_at':reading.now(),
         'protected_unchanged':before==after,'implementation_unchanged':frozen==implementation(),'published':False,
         'reviews':reviews,'note':'Browser state changes and model review do not alone prove numeric or educational correctness; inspect retained evidence.'})
    print('ALL EIGHT TESTS FINISHED',flush=True)


if __name__=='__main__': main()
