"""Summarize recorded real-model benchmark evidence without rerunning the product.

Reads only public-test artifacts. Writes docs/LIVE-BOUNDARY-REPORT.md.
Running/absent cases stay pending. Model review is never called human certification.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "data" / "benchmark-live"


def read(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def safe(value, limit=600):
    text = str(value).replace("\n", " ").replace("|", " / ")
    text = re.sub(r"sk-[A-Za-z0-9_-]+", "[redacted]", text)
    text = re.sub(r"(?i)(api[_-]?key|authorization|bearer)\s*[:=]\s*\S+", r"\1=[redacted]", text)
    return text[:limit]


def verdict(value):
    if value is None:
        return "未测/未记录"
    if isinstance(value, bool):
        return "通过" if value else "未通过"
    if isinstance(value, str):
        return safe(value)
    if isinstance(value, dict):
        return safe(value.get("verdict", value.get("status", "有记录，见原始结果")))
    return safe(value)


def gather(case):
    result = read(RESULTS / (case["id"] + ".json"), {})
    retest = read(ROOT/'data'/'benchmark-after-fixes'/(case['id']+'.json'))
    if retest and retest.get('status') != 'running':result=retest
    run = ROOT / "data" / "runs" / result.get("job_id", "__pending__")
    ir = read(run / "document-ir.json", {})
    plan = read(run / "plan.json", {})
    raw_reviews = []
    draft_nodes = []
    for path in sorted(run.glob("review-*.json")):
        raw_reviews.extend(read(path, {}).get("items", []))
    for path in sorted(run.glob("nodes-*.json")):
        draft_nodes.extend(read(path, {}).get("nodes", []))
    reviews = (result.get("verification") or {}).get("items", raw_reviews)
    checks = result.get("checks", {})
    coverage = (result.get("verification") or {}).get("coverage") or read(run / "coverage.json", {})
    if coverage == "pending":
        coverage = {}
    return dict(case=case, result=result, run=run, ir=ir, plan=plan, checks=checks,
                reviews=reviews, coverage=coverage, draft_nodes=draft_nodes,
                repairs=list(run.glob("repair-*.json")), rechecks=list(run.glob("recheck-*.json")))


def snapshot_table(rows):
    lines = ["| 文献 / 页数 | 测试流程 / 生成终态 | 节点 / 模型支持 | 图表观察页 / OCR页 | 引用契约 / 核心覆盖 | 修复 / 复查产物 |",
             "|---|---|---|---|---|---|"]
    for row in rows:
        c, r, ir, chk = row["case"], row["result"], row["ir"], row["checks"]
        running = r.get("status") == "running"
        nodes = r.get("nodes", len(row["draft_nodes"]) if row["draft_nodes"] else "待定")
        counts = Counter(v.get("verdict", "unknown") for v in row["reviews"])
        support = f"{counts['supported']}/{sum(counts.values())}" if counts else "待核验"
        if running and counts:
            support += "（暂存）"
        visual_pages = [str(v.get("page", "?")) for v in ir.get("visuals", []) if v.get("chart_or_table")]
        ocr = (r.get("parser") or {}).get("ocr_pages", ir.get("ocr_pages", "未记录"))
        contract = chk.get("reference_contract", {})
        ref = contract.get("schema", "未测")
        if contract.get("missing_source_ids"):
            ref += "/缺失引用"
        coverage = verdict(row["coverage"]) if row["coverage"] else "待核验"
        lines.append(f"| `{c['id']}` · {c['page_count']} | {r.get('status','未启动')} / {r.get('generation_status','未结束/未记录')} | {nodes} / {support} | {','.join(visual_pages) or '未记录'} / {ocr} | {ref} / {coverage} | {len(row['repairs'])} / {len(row['rechecks'])} |")
    return lines


def source_audit():
    """Recompute presence of sampled original passages, never infer scientific truth."""
    try:
        import pymupdf
    except ImportError:
        return ["原 PDF 抽查依赖 pymupdf，本次报告环境缺失；下列既有人工抽样结论未自动复核。"]
    checks = [("attention", 1, "41.8"), ("attention", 8, "41.0"), ("attention", 8, "41.8"),
              ("lyrics", 4, "840 billion tokes"), ("generative-ai-work", 1, "5,179"),
              ("generative-ai-work", 11, "5,179"), ("generative-ai-work", 43, "5,179"),
              ("cnnic55", 23, "110833"), ("cnnic55", 23, "78.6%")]
    lines = []
    for name, page, needle in checks:
        try:
            with pymupdf.open(ROOT / "data" / "test-corpus" / (name + ".pdf")) as doc:
                found = needle in doc[page - 1].get_text()
            lines.append(f"`{name}` PDF 第 {page} 页：`{needle}` → {'找到原文' if found else '未找到，需重查版本/抽取'}。")
        except Exception as error:
            lines.append(f"`{name}` 原文复核失败：{safe(error)}。")
    return lines


def main():
    manifest = read(ROOT / "tests" / "corpus" / "manifest.json", {"papers": []})
    rows = [gather(case) for case in manifest["papers"]]
    probe = read(ROOT / "data" / "live-probe.json", {})
    state = Counter(row["result"].get("generation_status", "pending") for row in rows)
    flow = Counter(row["result"].get("status", "not_started") for row in rows)
    now = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")
    lines = ["# paperMind 真实接入与跨领域边界测试", "", f"报告快照：{now}（Asia/Shanghai）。由 `python scripts/report_benchmark.py` 读取本地实测记录生成；不发起新的模型调用。", "",
             f"独立语料 {len(rows)} 篇。生成结果：ready={state['ready']}，incomplete={state['incomplete']}，failed={state['failed']}，未形成终态记录={state['pending']}。测试流程：tested={flow['tested']}，failed={flow['failed']}，running={flow['running']}，尚无当前记录={flow['not_started']}。", "",
             "`tested` 只表示测试脚本走完，不代表生成 ready，更不代表内容全部正确。运行未结束的行是阶段快照。`supported` / `covered` 是模型与给定来源的对照结果，不是人工学术审查、论文结论认证或独立复现实验。引用契约通过只证明格式/引用ID关系；不证明引用足以支持论断。", "",
             "主表读取 `data/benchmark-live/{id}.json`；已有完成的集中修复复测时，改用 `data/benchmark-after-fixes/{id}.json`。首轮完整快照保存在 `data/benchmark-live/first-pass/`，当时 8 ready、2 incomplete。早期两篇开发迭代另列。每篇原始产物只按所选记录的 `job_id` 取自 `data/runs/`，不混用旧任务成功产物。", "", "## 当前生成快照", ""]
    lines += snapshot_table(rows)
    lines += ["", "图表页指视觉模型实际生成并判为图/表的整页观察，不等于所有图表已覆盖；OCR页指记录中的 OCR 页面数。修复数为 repair JSON 产物个数，可能尚未通过复查；最终是否被接受须看节点 review 的 `repair_attempted` 与 verdict。", "", "## 对话、外部取证与事务检查", "",
              "| 文献 | 原文问答核验 / 引用数 | 视觉问答 | 外部取证核验 / 取证详情 | 页面修改撤回 / 概念保存 |", "|---|---|---|---|---|"]
    for row in rows:
        chk = row["checks"]
        qa = chk.get("copilot", {})
        visual = chk.get("visual_question")
        ext = chk.get("external_knowledge")
        search = ext.get("search", {}) if isinstance(ext, dict) else {}
        details = "; ".join(f"{k}={safe(v,100)}" for k,v in search.items() if k in {"search_result_count", "query", "error", "status"})
        fetch_errors = search.get("fetch_errors", [])
        if fetch_errors:
            details += f"; fetch失败={len(fetch_errors)}"
        if isinstance(ext, dict) and ext.get("source_ids") is not None:
            details += f"; 回答引用={len(ext['source_ids'])}"
        lines.append(f"| `{row['case']['id']}` | {verdict(qa.get('verification'))} / {qa.get('source_count','未记录')} | {verdict(visual.get('verification') if isinstance(visual,dict) else visual)} | {verdict(ext.get('verification') if isinstance(ext,dict) else ext)} / {safe(details) or '未记录'} | {verdict(chk.get('patch_roundtrip'))} / {verdict(chk.get('concept_save'))} |")
    lines += ["", "外部来源被成功下载或被模型判 supported，不自动等于权威定义已找到；还需检查来源机构、原文、版本及对具体断言的支持。`blocked_by_answer_verification` 是系统拒绝将未核验回答写入页面，不是撤回流程通过。概念保存检查只验证自报声明与保存动作，不证明跨论文层级复用已测试。", "", "## 用量、耗时和模型", "",
              "| 文献 | 生成秒 / 测试流程秒 | 模型调用数 / total_tokens | 实际返回模型 |", "|---|---|---|---|"]
    for row in rows:
        r = row["result"]
        met = r.get("metrics", {})
        lines.append(f"| `{row['case']['id']}` | {r.get('generation_seconds','未结束/未记录')} / {r.get('elapsed_seconds','未结束/未记录')} | {met.get('calls','未记录')} / {met.get('total_tokens','未记录')} | {', '.join(met.get('models',[])) or '未完成用量快照'} |")
    lines += ["", "用量 API 按 document_id 累计，可能含首次迭代、重试和后续问答，不是本轮单个 job 的净消耗。call_seconds 是调用耗时求和，不能当作用户等待的墙钟时间。供应商 usage 的 total_tokens 不换算费用；未取得账单/单价证据时不估报实际费用。", "",
              "配置的模型角色（不等于每篇均实际调用）：", "", "```json", json.dumps(probe.get("models",{}),ensure_ascii=False,indent=2), "```", "", "连接探针："]
    for key, value in probe.get("checks", {}).items():
        lines.append(f"- `{key}`：{'成功' if value.get('ok') else '失败'}。")
    web = probe.get("checks", {}).get("web_search_and_fetch", {}).get("result", {})
    if web:
        lines += ["", f"首次联网探针返回 {web.get('search_result_count','?')} 条搜索结果，成功取得 {len(web.get('sources',[]))} 个来源正文，失败 {len(web.get('fetch_errors',[]))} 个。该次可读结果为博客，不能写成已获取原始论文/大学权威依据。这体现搜索已接通与权威取证成功是两项不同能力。"]
    lines += ["", "## 首次迭代与当前结果对照", "", "| 文献 | 首次测试 / 生成 / 模型支持 | 当前测试 / 生成 / 模型支持 |", "|---|---|---|"]
    for path in sorted(RESULTS.glob("*-iteration1.json")):
        old = read(path,{})
        row = next((r for r in rows if r["case"]["id"] == old.get("case_id")),None)
        if not row:
            continue
        prior = (old.get("verification") or {}).get("items",[])
        old_supported=sum(v.get("verdict")=="supported" for v in prior)
        new_supported=sum(v.get("verdict")=="supported" for v in row["reviews"])
        r=row["result"]
        lines.append(f"| `{old['case_id']}` | {old.get('status')} / {old.get('generation_status')} / {old_supported}/{len(prior)} | {r.get('status','未开始')} / {r.get('generation_status','未结束')} / {new_supported}/{len(row['reviews'])} |")
    lines += ["", "首次迭代暴露的核验误报不能通过删掉失败记录掩盖；当前改进结果若尚未完成，不以预计修复代替实测。", "", "## 原始 PDF 抽样回查", "",
              "这是对四篇材料的明确问题进行原文抽样，读取 PDF 全文后定位相关段落；不是 10 篇全文逐句学术认证。页码均为 PDF 物理页序，另标印刷页码。", "",
              "### Attention：41.8 与 41.0 的确存在内部不一致", "",
              "所下载 arXiv 1706.03762v7：PDF 第 1 页摘要写 `a new single-model state-of-the-art BLEU score of 41.8`；第 8 页 Table 2 的 `Transformer (big)` 行 En-Fr 栏为 `41.8`；同页 §6.1 正文写 `our big model achieves a BLEU score of 41.0`。首次核验器指出这一冲突有原文支持，不是凭空误读。应忠实列出两处值与位置、标记原稿未解释，不自行决定哪个值是真值，也不把这种披露后的不确定性误判成讲解缺失。", "",
              "### Lyrics：840 billion 的“可疑笔误”判断是无根据的误报", "",
              "PDF 第 4 页左栏明确写：`Our song lyrics dataset comprises of roughly 50 million tokes. This dataset is too small as compared to the dataset used by Caliskan et al. that contains over 840 billion tokes.` 原文 `tokes` 为拼写形式，数值 `840 billion` 清楚可读。上一段说明 CA 来自 Caliskan 的 `a large internet crawl text corpus`。因此不能凭“通用语料通常没这么大”的常识把 840 billion 判为论文笔误或覆盖缺口。", "",
              "精确边界：本篇相关段落使用 internet crawl，未明确写出专名 Common Crawl；不能把对引用文献的领域知识冒充本篇逐字原文。此次只确认本篇确实陈述了这个数值与语料比较，不等于独立审计 Caliskan 原始语料的计数、词元定义或数据生产流程。首次结果还把作者明示的局限/未提供底层公式误当成讲解覆盖缺口，说明需要区分忠实转述、教学补充和外部学术批评。", "",
              "### Generative AI at Work：5,179 属于上传的 2023 版本", "",
              "上传的 arXiv 2304.11771v1，PDF 第 1 页题头 April 25, 2023；摘要为 `data from 5,179 customer support agents`，并写平均 `14 percent`。第 11 页再次写 `3 million chats by 5,179 agents`；第 43 页 Table 1 的 All / Agents 为 `5,179`。全文检索未出现 `5,172`。Stanford 的 [2025 QJE 期刊版条目](https://www.gsb.stanford.edu/faculty-research/publications/generative-ai-work) 使用 5,172，这属于版本差异；联网查到较新版本后也不能静默改上传稿的样本数。", "",
              "### CNNIC：亿、万人、百分比与百分点不可混淆", "",
              "第55次报告 PDF 第 7 页（印刷第 1 页）核心数据及第 23 页（印刷第 17 页）正文：截至 2024 年 12 月网民 `11.08 亿人`，较 2023 年 12 月增长 `1608 万人`，普及率 `78.6%`，提升 `1.1 个百分点`。第 23 页图 10 左轴明确是 `网民规模（万人，左轴）`，2024 年末为 `110833`，右轴为普及率 `78.6%`；110833 万人 = 11.0833 亿人，正文 11.08 亿是取整，并非内部冲突。2023 的 109225 万人到 110833 万人相差 1608 万人；77.5% 到 78.6% 相差 1.1 个百分点，不能写成增长 1.1%。数据截至 2024.12，不能被当前年度网络数据覆盖。", "",
              "本次报告生成时的原文字符串复核：", ""]
    lines += ["- "+line for line in source_audit()]
    lines += ["", "## 各篇仍需关注的边界与缺口", ""]
    for row in rows:
        c,r=row["case"],row["result"]
        lines += [f"### {c['id']}", "", "测试目的："+"；".join(c.get("boundaries",[]))+"。"]
        gaps = r.get("generation_gaps",[])
        if not gaps and row["plan"]:
            gaps = row["plan"].get("core_gaps",[])
        for gap in gaps:
            lines.append("- 记录的缺口："+safe(gap.get("reason",gap) if isinstance(gap,dict) else gap))
        issues = [issue for rev in row["reviews"] for issue in rev.get("issues",[])]
        for issue in issues[:6]:
            lines.append("- 模型复核问题（待人工判断）："+safe(issue))
        for error in r.get("errors",[]):
            lines.append("- 测试错误："+safe(error))
        if r.get("status") in {None,"running"}:
            lines.append("- 当前任务尚无完整测试终态，不能据此判断产品成功或失败。")
        lines.append("")
    lines += ["## 派生 OCR 与额外真实链路", ""]
    scan=read(RESULTS/'attention-page3-scan.json',{})
    if scan:
        scan_parser=scan.get('parser') or {}
        lines += [f"Attention 第3页栅格派生样本：{scan.get('generation_status')}，实际 OCR {scan_parser.get('ocr_pages','未记录')} 页。该文件仅一页，不是第11篇论文。OCR已获得文字，后续模型把整篇其他章节的公式要求加到该页，导致 coverage 缺口；保留 incomplete，不将识别成功写成整篇通过。", ""]
    supplement=read(RESULTS/'supplement-before-fixes.json',{})
    for test in supplement.get('results',[]):
        value=test.get('result',{})
        detail=''
        if test['name']=='real_attached_comparison':detail=f"分别引用两篇={value.get('cites_both')}，模型对照={verdict(value.get('answer',{}).get('verification'))}"
        elif 'cards' in value:detail='两层解释='+','.join(verdict(c.get('verification')) for c in value['cards'])+'；引用为上传论文，不能声称原文外知识已取证'
        else:detail='；'.join(f'{k}={safe(v,120)}' for k,v in value.items() if k!='external_knowledge')
        lines.append(f"- `{test['name']}`：{test['status']}。{detail}")
    lines += ["", "集中修复后的定向实测（与首轮分开）：", ""]
    edge=read(ROOT/'data'/'benchmark-after-fixes'/'edge-retests.json',{})
    for test in edge.get('tests',[]):
        value=test.get('result',{});card=value.get('card',{})
        detail=f"模型核验={verdict(value.get('verification') or card.get('verification'))}"
        if card:detail+=f"；引用外部正文={value.get('cites_external')}；实际读取外部来源={len(value.get('fetched_external_sources',[]))}"
        lines.append(f"- `{test['name']}`：{test['status']}，{detail}。{safe(test.get('error',''))}")
    final_api=read(ROOT/'data'/'benchmark-after-fixes'/'final-api-smoke.json',{})
    lines += ["", "最终 HTTP 接口复测（最新服务进程）：", ""]
    for test in final_api.get('tests',[]):
        value=test.get('result',{});answer=value.get('assistant',value)
        detail=f"HTTP {test['http']}；模型对照={verdict(answer.get('verification'))}"
        if 'cites_external' in test:detail+=f"；引用外部正文={test['cites_external']}"
        lines.append(f"- `{test['name']}`：{detail}。")
        for source in test.get('cited_external_sources',[]):lines.append(f"  - 实际引用：{source['url']}。{source['locator']}。")
    if final_api:
        lines += ["", "外部知识成功案例的正文已检查：实际讲解了 word2vec 负采样的正负样本、sigmoid 判别目标和噪声抽样，明确是歌词论文未展开的外部知识；最终引用 Goldberg & Levy (2014)、Landgraf & Bellay (2017) 的实际 PDF 正文。此前两次取证失败/仅说明不足的回答仍保留，不能把 supported 的拒答算成知识补充成功。", "",
                  "CNNIC 单位提问返回 11.08 亿、1608 万、78.6%、1.1 个百分点，区分了百分比/百分点；但将正文约数换算为‘即110800万人’，未主动标注其为四舍五入值。图表精确值为110833万人。该精度提示不足仍保留为边界，不能因模型判supported就省略回查。"]
    browser=read(ROOT/'artifacts'/'boundary-browser.json',{})
    if browser:lines += ["",f"修复前10篇浏览器页面检查：{len(browser.get('checks',[]))} 篇；页面运行错误 {len(browser.get('errors',[]))} 条。每篇原 PDF 可打开；CNNIC 生成区无节点，已记问题，不能计为讲解成功。覆盖 1440/736/390/320 阅读区宽度。"]
    live_browser=read(ROOT/'artifacts'/'live-browser-report.json',{})
    if live_browser:lines += [f"真实模型浏览器交互：{live_browser.get('status')}，{len(live_browser.get('checks',[]))} 组，包含框选和模型驱动演示回执。"]
    fixed_ui=read(ROOT/'artifacts'/'fixed-ui-report.json',{})
    if fixed_ui:lines += [f"失败状态与75页报告页面的修复复测：{fixed_ui.get('status')}，{len(fixed_ui.get('checks',[]))}组，错误{len(fixed_ui.get('errors',[]))}条。"]
    lines += ["", "详细问题及修复/未解决状态见 `docs/FIRST-PASS-ISSUES.md`。离线回归21项通过；TypeScript检查与构建通过。教学浏览器回归7组通过。以上不替代真实论文内容核验。", "", "## 覆盖范围的限制", "",
              "当前上传上限20MB/120页；默认OCR30页、视觉预读2页，可配置。外部PDF仅读取前12页，来源记录读取范围。本机单用户，无多人账号隔离。概念层级复用基于领域/标题/层级键，尚不具备完整语义等价匹配。", "",
              "本轮 10 篇为公开英文/中文数字 PDF、5–75 页，不能代表付费文献、加密文件、复杂扫描、超长书籍、手写、损坏文件、跨语种所有字体或所有学科。仅另有一页清晰栅格 OCR 样本；单页成功不等于多页扫描论文已端到端通过。", "",
              "当前自动流程验证的是解析、生成、引用契约、模型对照、部分问答与保存/撤回链路。学术真实性、交互教学有效性、每个图表的逐项数据准确率、用户独立理解、浏览器全部路径、跨论文知识迁移和长期可靠性需要各自额外证据。没有人工全量标注与盲审，就不报告虚假的学术准确率。", ""]
    target=ROOT/"docs"/"LIVE-BOUNDARY-REPORT.md"
    target.write_text("\n".join(lines),encoding="utf-8")
    print(f"Report written: {target}")
    print(f"Current: ready={state['ready']} incomplete={state['incomplete']} running={flow['running']} not_started={flow['not_started']}")


if __name__ == "__main__":
    main()
