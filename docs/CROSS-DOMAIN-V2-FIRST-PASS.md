# 跨领域 V2 首轮测试（排除 CNNIC）

更新时间：2026-10-25T07:22:10.946933+00:00。状态更正：本批已中断，8篇未全部完成。以下为首轮历史记录。

**后续状态：** RAG、5G完成首轮后失败；Shannon与歌词任务中断；其余4篇未启动。按用户最新要求转入已知问题修复和默认页发布，见 [V2修复发布记录](READING-V2-RELEASE.md)。没有后台批次继续运行。

范围为原测试集其余 8 篇；Attention 已有独立验收，本轮不重复，CNNIC 按用户要求排除，派生扫描样本不作为另一篇。
冻结生成链路和提示词；每篇首轮失败后保留产物继续下一篇，不修复、不重生失败篇、不升级为 validated、不发布默认呈现。
真实阿里模型：qwen3.5-plus 规划/编写，qwen3-vl-plus 原页识别/截图评审，qwen-plus 内容复核。2 个文档工作线程共用最多 3 个模型调用。

| 材料 | 页数 | 生成状态 | 生成用时 | 浏览器检查 | 模型事实审阅 |
|---|---:|---|---:|---|---|
| rag | 19 | 生成失败 | 16.0 分钟 | 隔离诊断：issues_recorded | 待执行/受阻 |
| adaptive-dcs-somp | 12 | 生成失败 | 10.6 分钟 | 隔离诊断：issues_recorded | 待执行/受阻 |
| shannon | 55 | 已中断 | — | 待执行 | 待执行/受阻 |
| lyrics | 5 | 已中断 | — | 待执行 | 待执行/受阻 |
| moral-machine | — | 未启动 | — | 待执行 | 待执行/受阻 |
| simulation-argument | — | 未启动 | — | 待执行 | 待执行/受阻 |
| generative-ai-work | — | 未启动 | — | 待执行 | 待执行/受阻 |
| macroeconomics-ai | — | 未启动 | — | 待执行 | 待执行/受阻 |

## 验收范围与判定限制

浏览器记录核心节点与来源 ID、实际控件操作轨迹、SVG/Canvas 或输出/表格/关系的变化、异常与非有限值、外部请求、736/390/320 像素布局；可用产品草稿另外检查右栏 Copilot 草稿、概念入口、目录、PDF 回跳位置和原讲解回退。不会发送问题或保存概念。
隔离诊断仅把保留的原始章节装入沙箱，不改变失败版本及其内容；绕过结构拦截用于排查后续故障，绝不算产品通过。诊断页不测试宿主上线可用性。
通用探针观察到变化不等于计算正确；纯高亮、折叠和解释文字变化需要结合原文与操作语义判断。拖拽/悬停等自定义行为可能需专门复核，不能据通用探针没有覆盖就宣称失效。
模型审阅使用完整 PDF 页文本和生成代码/实际轨迹，按材料独立核对数值或逻辑；截图审阅覆盖少量代表视口。模型意见保留原文，属于待核实发现，不作为独立发布门禁的替代。

## 分材料问题记录

### rag

生成状态：failed。

生成错误（未修复）：

```text
章节结构检查失败：[{"chapter": "chap-1-problem", "issue": "缺少节点锚点：{'problem-statement'}"}, {"chapter": "chap-2-architecture", "issue": "不允许的标签：pattern；不允许的标签：code"}, {"chapter": "chap-3-mechanism", "issue": "不允许的标签：lineargradient；不允许的标签：stop；不允许的标签：stop"}, {"chapter": "chap-4-training", "issue": "缺少节点锚点：{'training-decoding'}"}, {"chapter": "chap-7-ablation", "issue": "缺少节点锚点：{'retrieval-ablations'}"}, {"chapter": "chap-8-dynamic", "issue": "缺少节点锚点：{'index-hot-swapping'}"}, {"chapter": "chap-9-limits", "issue": "缺少节点锚点：{'limitations-scope'}"}]
```

浏览器观测：

- initialization：locator.waitFor: Timeout 12000ms exceeded. Call log: [2m  - waiting for locator('iframe').contentFrame().locator('body[data-pm-ready=true]') to be visible[22m 

原始证据：[本篇生成记录](../artifacts/reading-v2/cross-domain-first/rag.json)，浏览器及模型记录在同名子目录。

### adaptive-dcs-somp

生成状态：failed。

生成错误（未修复）：

```text
章节结构检查失败：[{"chapter": "chap-1-problem", "issue": "缺少节点锚点：{'problem-statement'}"}, {"chapter": "chap-2-model", "issue": "缺少节点锚点：{'system-model-3d'}"}, {"chapter": "chap-3-bottleneck", "issue": "缺少节点锚点：{'sensing-matrix-construction'}"}, {"chapter": "chap-4-mechanism", "issue": "不允许的标签：code；不允许的标签：code；不允许的标签：code；不允许的标签：code；不允许的标签：code；不允许的标签：code；不允许的标签：code；不允许的标签：code；不允许的标签：code；缺少节点锚点：{'adaptive-mechanism'}"}, {"chapter": "chap-7-limits", "issue": "缺少节点锚点：{'limitations-scope'}"}]
```

工程原文回查（已核对保留的原页、代码与轨迹）：

- [blocker] chap-3-bottleneck / initial sensing-matrix formula：Matrix multiplication inside the transposed term was replaced with another Kronecker product; expression is not the source equation.
- [blocker] chap-3-bottleneck / matrix-cols：Element calculation uses q^4 and approximately matches independent arithmetic; visible column count uses q^2 and contradicts both formula and element count.
- [blocker] chap-3-bottleneck / thresholdQ and chapter summary：UI labels q=18 as memory-overflow critical threshold and calls q^4 growth exponential. Source describes sensitivity and Figure2 hardware setup; this chapter does not establish hardware capacity justifying a universal q=18 cutoff. q^4 is polynomial growth. Generated limitations mention hardware but do not substantiate the cutoff.
- 探针判定限制：meaningful interaction chapter-chap-2-model — First generic pass did not select .term[data-highlight] or legend mouseenter. Do not conclude chapter has no interaction from operated=0.
- 探针判定限制：canvas pointer intercepted — Canvas overlays were active after preceding toggle/step probes; inspect intended use before treating blocked direct canvas clicks as a product bug.

浏览器观测：

- node coverage, visible content and source IDs：empty or missing canonical node
- meaningful interaction chapter-chap-2-model：No observed graphic, output data or relationship change. Inspect text-only traces before judging educational value.
- control chapter-chap-5-algo chap-5-algo-canvas：locator.click: Timeout 2200ms exceeded. Call log: [2m  - waiting for locator('iframe').contentFrame().locator('#chapter-chap-5-algo').locator('[data-pm-probe="probe-3"]')[22m [2m    - locator resolved to <canvas width="600" height="400" id="chap-5-algo-canvas" data-pm-probe="probe-3"></canvas>[22m [2m  - attempting click action[22m [2m    2 × waiting for element to be visible, enabled and stable[22m [2m      - element is visible, enabled and stable[22m [2m      - scrolling into view if needed[22m [2m      - done scrolling[22m [2m      - <div id="chap-5-algo-overlay" class="algo-overlay active">…</div> intercepts pointer events[22m [2m    - retrying click action[22m [2m    - waiting 20ms[22m [2m    2 × waiting for element to be visible, enabled and stable[22m [2m      - element is visible, enabled and stable[22m [2m      - scrolling into view if needed[22m [2m      - done scrolling[22m [2m      - <div id="chap-5-algo-overlay" class="algo-overlay active">…</div> intercepts pointer events[22m [2m    - retrying click action[22m [2m      - waiting 100ms[22m [2m    - waiting for element to be visible, enabled and stable[22m [2m    - element is visible, enabled and stable[22m [2m    - scrolling into view if needed[22m [2m    - done scrolling[22m [2m    - <div id="chap-5-algo-overlay" class="algo-overlay active">…</div> intercepts pointer events[22m [2m  - retrying click action[22m [2m    - waiting 500ms[22m [2m    - waiting for element to be visible, enabled and stable[22m [2m    - element is visible, enabled and stable[22m [2m 
- control chapter-chap-7-limits limit-canvas：locator.click: Timeout 2200ms exceeded. Call log: [2m  - waiting for locator('iframe').contentFrame().locator('#chapter-chap-7-limits').locator('[data-pm-probe="probe-2"]')[22m [2m    - locator resolved to <canvas width="400" height="300" id="limit-canvas" data-pm-probe="probe-2" aria-label="时钟偏差与多路径效应示意图"></canvas>[22m [2m  - attempting click action[22m [2m    2 × waiting for element to be visible, enabled and stable[22m [2m      - element is visible, enabled and stable[22m [2m      - scrolling into view if needed[22m [2m      - done scrolling[22m [2m      - <div id="viz-overlay" class="viz-overlay hidden visible">…</div> intercepts pointer events[22m [2m    - retrying click action[22m [2m    - waiting 20ms[22m [2m    2 × waiting for element to be visible, enabled and stable[22m [2m      - element is visible, enabled and stable[22m [2m      - scrolling into view if needed[22m [2m      - done scrolling[22m [2m      - <div id="viz-overlay" class="viz-overlay hidden visible">…</div> intercepts pointer events[22m [2m    - retrying click action[22m [2m      - waiting 100ms[22m [2m    2 × waiting for element to be visible, enabled and stable[22m [2m      - element is visible, enabled and stable[22m [2m      - scrolling into view if needed[22m [2m      - done scrolling[22m [2m      - <div id="viz-overlay" class="viz-overlay hidden visible">…</div> intercepts pointer events[22m [2m    - retrying click action[22m [2m      - waiting 500ms[22m 
- responsive 320：{"viewport":304,"scrollWidth":368,"overflow":[{"id":"chapter-chap-2-model","client":268,"scroll":274},{"id":"chapter-chap-3-bottleneck","client":268,"scroll":329},{"id":"chapter-chap-5-algo","client":268,"scroll":350}]}
- runtime errors, finite outputs and no external requests：h is not defined

原始证据：[本篇生成记录](../artifacts/reading-v2/cross-domain-first/adaptive-dcs-somp.json)，浏览器及模型记录在同名子目录。

### shannon

生成状态：running。

原始证据：[本篇生成记录](../artifacts/reading-v2/cross-domain-first/shannon.json)，浏览器及模型记录在同名子目录。

### lyrics

生成状态：running。

原始证据：[本篇生成记录](../artifacts/reading-v2/cross-domain-first/lyrics.json)，浏览器及模型记录在同名子目录。

### moral-machine

生成状态：queued。

原始证据：[本篇生成记录](../artifacts/reading-v2/cross-domain-first/moral-machine.json)，浏览器及模型记录在同名子目录。

### simulation-argument

生成状态：queued。

原始证据：[本篇生成记录](../artifacts/reading-v2/cross-domain-first/simulation-argument.json)，浏览器及模型记录在同名子目录。

### generative-ai-work

生成状态：queued。

原始证据：[本篇生成记录](../artifacts/reading-v2/cross-domain-first/generative-ai-work.json)，浏览器及模型记录在同名子目录。

### macroeconomics-ai

生成状态：queued。

原始证据：[本篇生成记录](../artifacts/reading-v2/cross-domain-first/macroeconomics-ai.json)，浏览器及模型记录在同名子目录。

## 跨材料设计隐患（源代码可复核，尚未修复）

- `backend/reading_v2_author.py` 的通用编写指令仍带有 Attention 专属 Table2/3/4、mask、dk=3、Q/K 三维的约束；通用 skill 结尾还要求训练策略/消融/泛化，可能影响其他学科内容选择。具体污染是否发生以逐篇原文回查为准。
- 编写器按 canonical 节点引用页分配原文证据，而视觉表格也按这些页过滤；可能使规划章节需要的其他证据不可见。
- 全文覆盖检查依赖锚点；有内容但漏锚点也会阻断整篇。不能用绕过检查作为修复。
- 视觉抽取依赖规划最多 4 页和英文 Table N: 页补齐，曲线、图示和复杂表头仍需核对，不能假定已自动准确抽取。

## 数据和版本保护

受保护表：documents/messages/patches/library/memories。首轮在中断时结束；修复发布批次另做了前后哈希核对，结果见修复发布记录。
此处描述的是中断前的冻结实现；之后的修复是独立批次，未覆盖首轮证据。
本轮不会自动推广默认呈现；已完成的 Attention 预览保持原版本。
