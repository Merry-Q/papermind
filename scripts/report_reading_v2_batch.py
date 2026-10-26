"""Summarize first-pass evidence without changing any product edition."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend import store, reading_v2
from benchmark_reading_v2 import CASES, protected, implementation


def load(path,default=None):
    try:return json.loads(path.read_text(encoding='utf-8'))
    except (FileNotFoundError,json.JSONDecodeError):return default


def main():
    p=argparse.ArgumentParser();p.add_argument('--batch',required=True);a=p.parse_args()
    out=store.ROOT/'artifacts/reading-v2'/a.batch
    finished=load(out/'verification-summary.json',{}).get('all_cases_finished',False)
    records=[load(out/(key+'.json'),{'case':key,'status':'queued'}) for key in CASES]
    lines=['# 跨领域 V2 首轮测试（排除 CNNIC）','',f'更新时间：{reading_v2.now()}。状态：'+('本批已完成。' if finished else '本批运行中，以下为增量记录。'),'',
      '范围为原测试集其余 8 篇；Attention 已有独立验收，本轮不重复，CNNIC 按用户要求排除，派生扫描样本不作为另一篇。',
      '冻结生成链路和提示词；每篇首轮失败后保留产物继续下一篇，不修复、不重生失败篇、不升级为 validated、不发布默认呈现。',
      '真实阿里模型：qwen3.5-plus 规划/编写，qwen3-vl-plus 原页识别/截图评审，qwen-plus 内容复核。2 个文档工作线程共用最多 3 个模型调用。','',
      '| 材料 | 页数 | 生成状态 | 生成用时 | 浏览器检查 | 模型事实审阅 |',
      '|---|---:|---|---:|---|---|']
    for v in records:
        key=v['case'];browser=load(out/key/'report.json',{});fidelity=load(out/key/'fidelity-review.json',{})
        diagnostic=(out/key/'diagnostic-scope.json').exists()
        state={'queued':'排队','running':'生成中','failed':'生成失败','draft':'草稿待验'}.get(v['status'],v['status'])
        browserstate=('隔离诊断：' if diagnostic else '')+browser.get('status', '生成失败，产品页面受阻' if v['status']=='failed' else '待执行')
        seconds=v.get('seconds');duration=f'{seconds/60:.1f} 分钟' if seconds is not None else '—'
        lines.append(f"| {key} | {v.get('pages','—')} | {state} | {duration} | {browserstate} | {fidelity.get('verdict','待执行/受阻')} |")
    lines+=['','## 验收范围与判定限制','',
      '浏览器记录核心节点与来源 ID、实际控件操作轨迹、SVG/Canvas 或输出/表格/关系的变化、异常与非有限值、外部请求、736/390/320 像素布局；可用产品草稿另外检查右栏 Copilot 草稿、概念入口、目录、PDF 回跳位置和原讲解回退。不会发送问题或保存概念。',
      '隔离诊断仅把保留的原始章节装入沙箱，不改变失败版本及其内容；绕过结构拦截用于排查后续故障，绝不算产品通过。诊断页不测试宿主上线可用性。',
      '通用探针观察到变化不等于计算正确；纯高亮、折叠和解释文字变化需要结合原文与操作语义判断。拖拽/悬停等自定义行为可能需专门复核，不能据通用探针没有覆盖就宣称失效。',
      '模型审阅使用完整 PDF 页文本和生成代码/实际轨迹，按材料独立核对数值或逻辑；截图审阅覆盖少量代表视口。模型意见保留原文，属于待核实发现，不作为独立发布门禁的替代。','',
      '## 分材料问题记录','']
    for v in records:
        key=v['case'];lines+=['### '+key,'']
        lines.append('生成状态：'+v['status']+'。')
        if v.get('error'):lines+=['','生成错误（未修复）：', '', '```text',v['error'],'```']
        engineering=load(out/key/'engineering-source-check.json',{})
        if engineering:
            lines+=['','工程原文回查（已核对保留的原页、代码与轨迹）：','']
            for finding in engineering.get('findings',[]):lines.append('- ['+finding['severity']+'] '+finding['location']+'：'+finding['detail'])
            for disposition in engineering.get('dispositions',[]):lines.append('- 探针判定限制：'+disposition['probe']+' — '+disposition['detail'])
        browser=load(out/key/'report.json',{})
        for label,items in [('浏览器观测',browser.get('issues',[])),('宿主观测',browser.get('host',{}).get('issues',[]))]:
            if items:
                lines+=['',label+'：','']
                for i in items:lines.append('- '+i['name']+'：'+i['detail'].replace('\n',' ')[:1600])
        for name,label in [('fidelity-review.json','模型内容复核（待原文回查）'),('experience-review.json','模型截图复核（待视觉回查）')]:
            review=load(out/key/name,{})
            if review:
                lines+=['',label+'：'+review['verdict'],'']
                for finding in review.get('findings',[]):lines.append('- ['+finding['severity']+'] '+finding['location']+'：'+finding['detail'])
        if v.get('preview_url'):lines+=['',f"[产品草稿预览]({v['preview_url']})（仅检查用，未验证/发布）。"]
        lines+=['',f"原始证据：[本篇生成记录](../artifacts/reading-v2/{a.batch}/{key}.json)，浏览器及模型记录在同名子目录。",'']
    lines+=['## 跨材料设计隐患（源代码可复核，尚未修复）','',
      '- `backend/reading_v2_author.py` 的通用编写指令仍带有 Attention 专属 Table2/3/4、mask、dk=3、Q/K 三维的约束；通用 skill 结尾还要求训练策略/消融/泛化，可能影响其他学科内容选择。具体污染是否发生以逐篇原文回查为准。',
      '- 编写器按 canonical 节点引用页分配原文证据，而视觉表格也按这些页过滤；可能使规划章节需要的其他证据不可见。',
      '- 全文覆盖检查依赖锚点；有内容但漏锚点也会阻断整篇。不能用绕过检查作为修复。',
      '- 视觉抽取依赖规划最多 4 页和英文 Table N: 页补齐，曲线、图示和复杂表头仍需核对，不能假定已自动准确抽取。','',
      '## 数据和版本保护','']
    before=load(out/'protected-before.json',{})
    after=load(out/'protected-after-tests.json',load(out/'protected-after-generation.json',{}))
    frozen=load(out/'implementation.json',{})
    lines.append('受保护表：documents/messages/patches/library/memories。'+('最终哈希一致。' if after and before==after else '最终比对待完成；增量测试不写这些表。'))
    lines.append('生成实现哈希：'+('与批次开始一致。' if frozen==implementation() else '存在变化，需复核 implementation.json。'))
    lines.append('本轮不会自动推广默认呈现；已完成的 Attention 预览保持原版本。')
    (store.ROOT/'docs/CROSS-DOMAIN-V2-FIRST-PASS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('REPORT UPDATED',sum(v['status'] not in ['queued','running'] for v in records),'of 8; finished',finished)


if __name__=='__main__':main()
