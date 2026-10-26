"""Frozen checks of the expanded corpus; never fixes, promotes or publishes."""
import base64
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend import reading_v2 as r, model_gateway as gateway, store, settings
from backend.reading_v2_contracts import ReadingReview
from extend_reading_v2 import OUT, CASES
from benchmark_reading_v2 import save
from verify_reading_v2_batch import CRITERIA, diagnostic

CRITERIA.update({
 'hyperbolic-location':'Chan与Ho双曲定位估计；TDOA噪声及协方差、两阶段加权最小二乘、平方变量约束与符号恢复、CRLB小噪声条件；教学几何不是原论文蒙特卡洛复现。',
 'transformer-excerpt':'只解释上传的单页架构图和文字；不要把未上传的完整Attention论文细节当缺页或实验事实；图中编码器、解码器、遮蔽注意力与残差归一化关系。',
 '5g-overview':'综述性技术探讨；区分作者所述技术趋势、运营商个别案例与真实实验；无原文数字不能编造精度对比或推导公式；PRS/PRSID与异构融合的适用范围。',
})


def command(args,dest,prefix):
    proc=subprocess.run(args,cwd=store.ROOT,capture_output=True,encoding='utf-8',errors='replace',timeout=900)
    (dest/(prefix+'.stdout.txt')).write_text(proc.stdout,encoding='utf-8')
    (dest/(prefix+'.stderr.txt')).write_text(proc.stderr,encoding='utf-8')
    return proc.returncode


def browser(value,phase='first-pass'):
    key=value['case'];dest=OUT/key/phase;dest.mkdir(exist_ok=True)
    candidate=r.folder(value['edition'])/'candidate.html' if value.get('edition') else None
    if value['status']!='draft':
        save(dest/'blocked.json',{'reason':value.get('error'),'edition':value.get('edition')})
        try:candidate=diagnostic(value,dest) if value.get('folder') else None
        except Exception as e:save(dest/'diagnostic-error.json',{'error':str(e)});candidate=None
        if not candidate:return
    try:
        probe='scripts/validate-reading-v2-material.mjs' if phase!='first-pass' else 'scripts/validate-reading-v2-generic.mjs'
        command(['node',probe,str(candidate),str(dest)],dest,'browser')
        if value['status']=='draft':
            host=dest/'host';host.mkdir(exist_ok=True)
            host_script='scripts/check-reading-v2-material-host.mjs' if phase!='first-pass' else 'scripts/check-reading-v2-draft-host.mjs'
            command(['node',host_script,value['document_id'],value['edition'],str(host)],dest,'host')
    except Exception as error:save(dest/'infrastructure-error.json',{'error':str(error)})
    print('BROWSER END',key,flush=True)


def review(value,phase='first-pass'):
    key=value['case'];dest=OUT/key/phase;dest.mkdir(exist_ok=True)
    if value['status']!='draft' and not (dest/'diagnostic-artifact.json').exists():return {'case':key,'status':'blocked'}
    f=r.folder(value['edition']);pack=json.loads((f/'evidence.json').read_text(encoding='utf-8'))
    artifact=json.loads((f/'artifact.json' if (f/'artifact.json').exists() else dest/'diagnostic-artifact.json').read_text(encoding='utf-8'))
    data=json.loads((f/'data.json').read_text(encoding='utf-8'))
    b=json.loads((dest/'report.json').read_text(encoding='utf-8')) if (dest/'report.json').exists() else {}
    traces=[{k:c.get(k) for k in ['chapter','id','label','traces','errors']} for c in b.get('controls',[])]
    evidence={'title':pack['title'],'focus':CRITERIA[key],'full_pdf_text':pack['pages'],
      'source_quotes':pack['sources'],'tables':data['tables'],'artifact':artifact,
      'operations':traces,'browser_issues':b.get('issues',[])}
    context={'feature':'reading.v2.other-materials-review','reading_edition_id':value['edition'],'case':key}
    results={'case':key,'edition':value['edition']}
    try:
        instruction=('对照本次实际上传版本逐章核验完整讲解、引用、公式、单位、条件。只报告生成作品与原文存在的具体矛盾、无依据事实、真实计算错误或缺失核心论证；'
         '每项必须给出生成位置、实际错误内容和原文物理页及证据。明确标注的教学参数不要求原文有同样数值，按所声明公式独立复算至少两个状态或逻辑分支，写入coverage。'
         '检查操作是否改变图形、数据或关系，文本变化不必然等于失败（逻辑推论本身可以是结果）。原文没有实验、统计检验、实现细节或更底层推导，不能因此判作品缺失或建议编造。'
         '不得依照其他版本/模型记忆推翻当前来源。默认展示已说明教学性质的局部模型，无需实现完整真实实验；不能把原文中的所有内容都强加为交互要求。'
         '只把导致核心概念或数值误解的问题标blocker，版式或非关键细节标minor；事实充分则pass。不要复述一般研究局限作为缺陷。给出实际核对的全篇主线和复算结果。')
        fidelity=gateway.structured('reviewer',instruction,evidence,ReadingReview,max_tokens=8500,context=context)
        save(dest/'fidelity-review.json',fidelity);results['fidelity']=fidelity['verdict']
    except Exception as error:
        results['fidelity_error']=settings.sanitize(error)
    shots=[dest/name for name in ['desktop-hero.png','chapter-0.png','chapter-2.png','chapter-4.png','mobile-hero.png'] if (dest/name).exists()]
    if shots:
        message=[{'type':'text','text':'核验这些论文交互讲解局部截图的可读性。只报告实际可见的重叠、截断、不可读图例和误导视觉。截图未拍到的内容不算缺失；默认状态的按钮禁用可能正常；不要求测验/评分。minor用于非关键美观建议，只有阻碍理解才blocker。输出JSON：'+store.encode(ReadingReview.model_json_schema())+'。论文：'+pack['title']}]
        for p in shots:message.extend([{'type':'text','text':p.name},{'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()}}])
        try:
            exp=ReadingReview.model_validate(gateway.request('vision',[{'role':'user','content':message}],max_tokens=5000,context=context)).model_dump()
            save(dest/'experience-review.json',exp);results['experience']=exp['verdict']
        except Exception as error:results['experience_error']=settings.sanitize(error)
    save(dest/'review-summary.json',results)
    print('REVIEW END',key,results,flush=True)
    return results


if __name__=='__main__':
    done=set();reviews=[];futures={}
    # Reviewer (qwen-plus) and visual checks have independent model quotas from
    # chapter authoring (qwen3.5-plus). Bound this process to two review tasks.
    with ThreadPoolExecutor(max_workers=2) as pool:
        while len(done)<len(CASES):
            for key,_,_ in CASES:
                p=OUT/key/'generation.json'
                if key in done or not p.exists():continue
                try:v=json.loads(p.read_text(encoding='utf-8'))
                except json.JSONDecodeError:continue
                if v.get('status') not in ['draft','failed']:continue
                if not (OUT/key/'first-pass'/'report.json').exists():browser(v)
                prior=OUT/key/'first-pass/review-summary.json'
                if prior.exists():reviews.append(json.loads(prior.read_text(encoding='utf-8')))
                else:futures[pool.submit(review,v)]=key
                done.add(key)
            for future in list(futures):
                if future.done():
                    reviews.append(future.result());del futures[future]
                    save(OUT/'review-summary.json',reviews)
            if len(done)<len(CASES):time.sleep(4)
        for future in as_completed(futures):
            reviews.append(future.result());save(OUT/'review-summary.json',reviews)
    save(OUT/'first-pass-complete.json',{'completed_at':r.now(),'all_cases_checked':True,'reviews':reviews,'repairs_started':False,'published':False})
    print('ALL FIRST-PASS CHECKS FINISHED',flush=True)
