# paperMind 真实接入与跨领域边界测试

报告快照：2026-10-25T00:36:46+08:00（Asia/Shanghai）。由 `python scripts/report_benchmark.py` 读取本地实测记录生成；不发起新的模型调用。

独立语料 10 篇。生成结果：ready=10，incomplete=0，failed=0，未形成终态记录=0。测试流程：tested=9，failed=1，running=0，尚无当前记录=0。

`tested` 只表示测试脚本走完，不代表生成 ready，更不代表内容全部正确。运行未结束的行是阶段快照。`supported` / `covered` 是模型与给定来源的对照结果，不是人工学术审查、论文结论认证或独立复现实验。引用契约通过只证明格式/引用ID关系；不证明引用足以支持论断。

主表读取 `data/benchmark-live/{id}.json`；已有完成的集中修复复测时，改用 `data/benchmark-after-fixes/{id}.json`。首轮完整快照保存在 `data/benchmark-live/first-pass/`，当时 8 ready、2 incomplete。早期两篇开发迭代另列。每篇原始产物只按所选记录的 `job_id` 取自 `data/runs/`，不混用旧任务成功产物。

## 当前生成快照

| 文献 / 页数 | 测试流程 / 生成终态 | 节点 / 模型支持 | 图表观察页 / OCR页 | 引用契约 / 核心覆盖 | 修复 / 复查产物 |
|---|---|---|---|---|---|
| `attention` · 15 | tested / ready | 10 / 10/10 | 13,14 / 0 | pass / covered | 1 / 1 |
| `rag` · 19 | tested / ready | 10 / 10/10 | 6,8 / 0 | pass / covered | 0 / 0 |
| `adaptive-dcs-somp` · 12 | tested / ready | 8 / 8/8 | 3 / 0 | pass / covered | 0 / 0 |
| `shannon` · 55 | tested / ready | 10 / 10/10 | 9,23 / 0 | pass / covered | 0 / 0 |
| `lyrics` · 5 | tested / ready | 10 / 10/10 | 3,4 / 0 | pass / covered | 1 / 1 |
| `moral-machine` · 17 | tested / ready | 8 / 8/8 | 4 / 0 | pass / covered | 0 / 0 |
| `simulation-argument` · 14 | failed / ready | 10 / 10/10 | 未记录 / 0 | pass / covered | 0 / 0 |
| `generative-ai-work` · 57 | tested / ready | 10 / 10/10 | 30,31 / 1 | pass / covered | 0 / 0 |
| `macroeconomics-ai` · 58 | tested / ready | 9 / 9/9 | 37,40 / 0 | pass / covered | 0 / 0 |
| `cnnic55` · 75 | tested / ready | 9 / 9/9 | 35,33 / 3 | pass / covered | 0 / 0 |

图表页指视觉模型实际生成并判为图/表的整页观察，不等于所有图表已覆盖；OCR页指记录中的 OCR 页面数。修复数为 repair JSON 产物个数，可能尚未通过复查；最终是否被接受须看节点 review 的 `repair_attempted` 与 verdict。

## 对话、外部取证与事务检查

| 文献 | 原文问答核验 / 引用数 | 视觉问答 | 外部取证核验 / 取证详情 | 页面修改撤回 / 概念保存 |
|---|---|---|---|---|
| `attention` | supported / 3 | supported | supported / query=self-attention scaling factor variance derivation softmax gradient vanishing "dot product attention"; search_result_count=20; fetch失败=20; 回答引用=2 | 通过 / 通过 |
| `rag` | supported / 2 | supported | insufficient / query=non-parametric memory definition neural networks textbook "memory networks" "retrieval-based memory"; search_result_count=20; fetch失败=19; 回答引用=3 | 通过 / 通过 |
| `adaptive-dcs-somp` | supported / 2 | supported | insufficient / query=Balanis "Antenna Theory: Analysis and Design" 4th edition uniform circular array definition; search_result_count=20; fetch失败=18; 回答引用=1 | 通过 / 通过 |
| `shannon` | supported / 3 | supported | supported / query=Shannon entropy definition rigorous mathematical foundation textbook source; search_result_count=6; fetch失败=2; 回答引用=3 | 通过 / 通过 |
| `lyrics` | supported / 1 | insufficient | insufficient / query=distributed representation word embedding definition textbook natural language processing; search_result_count=19; fetch失败=19; 回答引用=2 | 通过 / 通过 |
| `moral-machine` | supported / 2 | supported | insufficient / query=Philippa Foot 1967 "The Problem of Abortion and the Doctrine of the Double Effect" moral dilemma def; search_result_count=10; fetch失败=2; 回答引用=3 | 通过 / 通过 |
| `simulation-argument` | insufficient / 2 | 未测/未记录 | 未测/未记录 / 未记录 | blocked_by_answer_verification / 通过 |
| `generative-ai-work` | insufficient / 2 | insufficient | insufficient / query=definition of "experience curve" in industrial organization textbook Porter or Boston Consulting Gro; search_result_count=14; fetch失败=12; 回答引用=2 | blocked_by_answer_verification / 通过 |
| `macroeconomics-ai` | supported / 24 | supported | insufficient / query=Hulten's Theorem original 1978 paper definition assumptions textbook exposition; search_result_count=8; fetch失败=3; 回答引用=4 | 通过 / 通过 |
| `cnnic55` | insufficient / 3 | supported | insufficient / query=CNNIC 网民定义 过去半年 使用互联网 官方定义 权威出处; search_result_count=20; fetch失败=16; 回答引用=3 | blocked_by_answer_verification / 通过 |

外部来源被成功下载或被模型判 supported，不自动等于权威定义已找到；还需检查来源机构、原文、版本及对具体断言的支持。`blocked_by_answer_verification` 是系统拒绝将未核验回答写入页面，不是撤回流程通过。概念保存检查只验证自报声明与保存动作，不证明跨论文层级复用已测试。

## 用量、耗时和模型

| 文献 | 生成秒 / 测试流程秒 | 模型调用数 / total_tokens | 实际返回模型 |
|---|---|---|---|
| `attention` | 399.19 / 847.52 | 38 / 523488 | qwen-plus, qwen3-vl-plus, qwen3.5-plus |
| `rag` | 347.84 / 508.78 | 22 / 331805 | qwen-plus, qwen3-vl-plus, qwen3.5-plus |
| `adaptive-dcs-somp` | 249.41 / 433.7 | 46 / 825359 | qwen-plus, qwen3-vl-plus, qwen3.5-plus |
| `shannon` | 415.09 / 728.69 | 23 / 628953 | qwen-plus, qwen3-vl-plus, qwen3.5-plus |
| `lyrics` | 311.72 / 699.38 | 34 / 407566 | qwen-plus, qwen3-vl-plus, qwen3.5-plus |
| `moral-machine` | 312.11 / 622.16 | 19 / 211186 | qwen-plus, qwen3-vl-plus, qwen3.5-plus |
| `simulation-argument` | 344.06 / 393.2 | 未记录 / 未记录 | 未完成用量快照 |
| `generative-ai-work` | 434.5 / 593.95 | 23 / 640448 | qwen-plus, qwen3-vl-plus, qwen3.5-ocr, qwen3.5-plus |
| `macroeconomics-ai` | 526.58 / 867.88 | 19 / 802243 | qwen-plus, qwen3-vl-plus, qwen3.5-plus |
| `cnnic55` | 740.19 / 871.72 | 35 / 1101847 | qwen-plus, qwen3-vl-plus, qwen3.5-ocr, qwen3.5-plus |

用量 API 按 document_id 累计，可能含首次迭代、重试和后续问答，不是本轮单个 job 的净消耗。call_seconds 是调用耗时求和，不能当作用户等待的墙钟时间。供应商 usage 的 total_tokens 不换算费用；未取得账单/单价证据时不估报实际费用。

配置的模型角色（不等于每篇均实际调用）：

```json
{
  "planner": "qwen3.5-plus",
  "composer": "qwen3.5-plus",
  "reviewer": "qwen-plus",
  "copilot": "qwen-plus",
  "vision": "qwen3-vl-plus",
  "ocr": "qwen3.5-ocr",
  "search": "qwen-plus"
}
```

连接探针：
- `planner_json`：成功。
- `dedicated_ocr`：成功。
- `web_search_and_fetch`：成功。

首次联网探针返回 10 条搜索结果，成功取得 1 个来源正文，失败 7 个。该次可读结果为博客，不能写成已获取原始论文/大学权威依据。这体现搜索已接通与权威取证成功是两项不同能力。

## 首次迭代与当前结果对照

| 文献 | 首次测试 / 生成 / 模型支持 | 当前测试 / 生成 / 模型支持 |
|---|---|---|
| `attention` | tested / incomplete / 9/10 | tested / ready / 10/10 |
| `lyrics` | tested / incomplete / 5/8 | tested / ready / 10/10 |

首次迭代暴露的核验误报不能通过删掉失败记录掩盖；当前改进结果若尚未完成，不以预计修复代替实测。

## 原始 PDF 抽样回查

这是对四篇材料的明确问题进行原文抽样，读取 PDF 全文后定位相关段落；不是 10 篇全文逐句学术认证。页码均为 PDF 物理页序，另标印刷页码。

### Attention：41.8 与 41.0 的确存在内部不一致

所下载 arXiv 1706.03762v7：PDF 第 1 页摘要写 `a new single-model state-of-the-art BLEU score of 41.8`；第 8 页 Table 2 的 `Transformer (big)` 行 En-Fr 栏为 `41.8`；同页 §6.1 正文写 `our big model achieves a BLEU score of 41.0`。首次核验器指出这一冲突有原文支持，不是凭空误读。应忠实列出两处值与位置、标记原稿未解释，不自行决定哪个值是真值，也不把这种披露后的不确定性误判成讲解缺失。

### Lyrics：840 billion 的“可疑笔误”判断是无根据的误报

PDF 第 4 页左栏明确写：`Our song lyrics dataset comprises of roughly 50 million tokes. This dataset is too small as compared to the dataset used by Caliskan et al. that contains over 840 billion tokes.` 原文 `tokes` 为拼写形式，数值 `840 billion` 清楚可读。上一段说明 CA 来自 Caliskan 的 `a large internet crawl text corpus`。因此不能凭“通用语料通常没这么大”的常识把 840 billion 判为论文笔误或覆盖缺口。

精确边界：本篇相关段落使用 internet crawl，未明确写出专名 Common Crawl；不能把对引用文献的领域知识冒充本篇逐字原文。此次只确认本篇确实陈述了这个数值与语料比较，不等于独立审计 Caliskan 原始语料的计数、词元定义或数据生产流程。首次结果还把作者明示的局限/未提供底层公式误当成讲解覆盖缺口，说明需要区分忠实转述、教学补充和外部学术批评。

### Generative AI at Work：5,179 属于上传的 2023 版本

上传的 arXiv 2304.11771v1，PDF 第 1 页题头 April 25, 2023；摘要为 `data from 5,179 customer support agents`，并写平均 `14 percent`。第 11 页再次写 `3 million chats by 5,179 agents`；第 43 页 Table 1 的 All / Agents 为 `5,179`。全文检索未出现 `5,172`。Stanford 的 [2025 QJE 期刊版条目](https://www.gsb.stanford.edu/faculty-research/publications/generative-ai-work) 使用 5,172，这属于版本差异；联网查到较新版本后也不能静默改上传稿的样本数。

### CNNIC：亿、万人、百分比与百分点不可混淆

第55次报告 PDF 第 7 页（印刷第 1 页）核心数据及第 23 页（印刷第 17 页）正文：截至 2024 年 12 月网民 `11.08 亿人`，较 2023 年 12 月增长 `1608 万人`，普及率 `78.6%`，提升 `1.1 个百分点`。第 23 页图 10 左轴明确是 `网民规模（万人，左轴）`，2024 年末为 `110833`，右轴为普及率 `78.6%`；110833 万人 = 11.0833 亿人，正文 11.08 亿是取整，并非内部冲突。2023 的 109225 万人到 110833 万人相差 1608 万人；77.5% 到 78.6% 相差 1.1 个百分点，不能写成增长 1.1%。数据截至 2024.12，不能被当前年度网络数据覆盖。

本次报告生成时的原文字符串复核：

- `attention` PDF 第 1 页：`41.8` → 找到原文。
- `attention` PDF 第 8 页：`41.0` → 找到原文。
- `attention` PDF 第 8 页：`41.8` → 找到原文。
- `lyrics` PDF 第 4 页：`840 billion tokes` → 找到原文。
- `generative-ai-work` PDF 第 1 页：`5,179` → 找到原文。
- `generative-ai-work` PDF 第 11 页：`5,179` → 找到原文。
- `generative-ai-work` PDF 第 43 页：`5,179` → 找到原文。
- `cnnic55` PDF 第 23 页：`110833` → 找到原文。
- `cnnic55` PDF 第 23 页：`78.6%` → 找到原文。

## 各篇仍需关注的边界与缺口

### attention

测试目的：双栏阅读顺序；注意力公式/矩阵维度；BLEU表格与训练设置；机制演示不冒充训练复现。

### rag

测试目的：概率分解与检索生成关系；主文与附录区分；跨论文概念复用；检索准确不等于生成事实正确。

### adaptive-dcs-somp

测试目的：稀疏恢复与通信前置知识；多层公式和符号；仿真曲线不等于真实部署；搜索域教学模型的边界。

### shannon

测试目的：长理论文档覆盖；定理与条件不可省略；熵公式与示意图；历史语境与后续知识分开。

### lyrics

测试目的：数字人文与文化语料；WEAT偏差指标；表格统计不能替代社会因果结论；短文完整论证。

### moral-machine

测试目的：图示情景与偏好统计；描述性伦理不等于规范性结论；文化聚类与样本选择；人数/决策次数/地域单位区别。
- 模型复核问题（待人工判断）：claim_age_preference_conflict 中引用的数值 '概率差 0.49' 在原文中明确标注为 AMCE（平均边际成分效应），其单位是概率差值，标准误 SE=0.0008；但原文未说明该数值是否直接等同于 '保全年轻角色的概率比保全老年角色高出 0.49' 这一通俗表述——AMCE 是在控制其他所有属性联合分布下的条件平均效应，而非无条件概率差。尽管该简化表述在科普语境中常见且合理，但严格而言，'0.49' 是模型估计的因果边际效应，非经验频率差；原文支持该 AMCE 值及其解释（Fig.2(a) 和 p5-b1），但未支持将 AMCE 等同于简单概率差的未经限定陈述。
- 模型复核问题（待人工判断）：claim_utilitarian_support 中'强烈支持牺牲少数以挽救多数的功利主义原则'属合理归纳，但原文仅指出公众对此有'强烈的共识支持'（p5-b1），并强调德国准则#9'留有余地'，未将该偏好命名为或归类为'功利主义原则'；术语'功利主义'未在所供原文段落中出现，属作者外加解释性标签，虽教学上可接受，但非原文直接支持的主张。

### simulation-argument

测试目的：纯理论哲学论证结构；三分命题不能误写成已证实生活在模拟中；概率公式的前提；没有实证图表时不得强造数值演示。
- 测试错误：HTTP 405: {"detail":"Method Not Allowed"}

### generative-ai-work

测试目的：长实证论文与附录；样本人数版本差异5179/5172；平均效果与异质性；相关性/因果识别与外推边界。

### macroeconomics-ai

测试目的：长理论加数据校准；模型假设与预测区间；GDP与TFP及时间尺度；与微观生产率研究比较不能直接等同。

### cnnic55

测试目的：中文长研报与目录页码；图表单位亿/万/百分比；统计时点及地域口径；描述性数据不可伪造因果关系。

## 派生 OCR 与额外真实链路

Attention 第3页栅格派生样本：incomplete，实际 OCR 1 页。该文件仅一页，不是第11篇论文。OCR已获得文字，后续模型把整篇其他章节的公式要求加到该页，导致 coverage 缺口；保留 incomplete，不将识别成功写成整篇通过。

- `real_attached_comparison`：tested。分别引用两篇=True，模型对照=supported
- `finish_philosophy`：tested。library_delete=preexisting_item_preserved；generation_status_unchanged=True
- `recursive_knowledge_two_layers`：tested。两层解释=supported,supported；引用为上传论文，不能声称原文外知识已取证
- `partial_cn_report`：tested。generation_status_unchanged=True
- `finish_scan`：tested。library_delete=preexisting_item_preserved；generation_status_unchanged=True

集中修复后的定向实测（与首轮分开）：

- `visual_answer_review_sees_actual_image`：tested，模型核验=supported。
- `knowledge_beyond_uploaded_paper_with_external_evidence`：tested，模型核验=insufficient；引用外部正文=True；实际读取外部来源=1。
- `philosophy_no_unwarranted_exclusivity`：tested，模型核验=supported。
- `external_knowledge_after_pdf_paragraph_fix`：tested，模型核验=supported；引用外部正文=False；实际读取外部来源=1。

最终 HTTP 接口复测（最新服务进程）：

- `external_knowledge_http_after_digit_fix`：HTTP 200；模型对照=supported；引用外部正文=True。
  - 实际引用：https://arxiv.org/pdf/1705.09755v1。PDF前5页，未读取其余页。
  - 实际引用：https://arxiv.org/pdf/1402.3722v1。PDF前5页，未读取其余页。
- `document_anchor_source_only_chat`：HTTP 201；模型对照=supported。
- `cnnic_units_and_percentage_points`：HTTP 201；模型对照=supported。

外部知识成功案例的正文已检查：实际讲解了 word2vec 负采样的正负样本、sigmoid 判别目标和噪声抽样，明确是歌词论文未展开的外部知识；最终引用 Goldberg & Levy (2014)、Landgraf & Bellay (2017) 的实际 PDF 正文。此前两次取证失败/仅说明不足的回答仍保留，不能把 supported 的拒答算成知识补充成功。

CNNIC 单位提问返回 11.08 亿、1608 万、78.6%、1.1 个百分点，区分了百分比/百分点；但将正文约数换算为‘即110800万人’，未主动标注其为四舍五入值。图表精确值为110833万人。该精度提示不足仍保留为边界，不能因模型判supported就省略回查。

修复前10篇浏览器页面检查：10 篇；页面运行错误 0 条。每篇原 PDF 可打开；CNNIC 生成区无节点，已记问题，不能计为讲解成功。覆盖 1440/736/390/320 阅读区宽度。
真实模型浏览器交互：passed，6 组，包含框选和模型驱动演示回执。
失败状态与75页报告页面的修复复测：passed，2组，错误0条。

详细问题及修复/未解决状态见 `docs/FIRST-PASS-ISSUES.md`。离线回归21项通过；TypeScript检查与构建通过。教学浏览器回归7组通过。以上不替代真实论文内容核验。

## 覆盖范围的限制

当前上传上限20MB/120页；默认OCR30页、视觉预读2页，可配置。外部PDF仅读取前12页，来源记录读取范围。本机单用户，无多人账号隔离。概念层级复用基于领域/标题/层级键，尚不具备完整语义等价匹配。

本轮 10 篇为公开英文/中文数字 PDF、5–75 页，不能代表付费文献、加密文件、复杂扫描、超长书籍、手写、损坏文件、跨语种所有字体或所有学科。仅另有一页清晰栅格 OCR 样本；单页成功不等于多页扫描论文已端到端通过。

当前自动流程验证的是解析、生成、引用契约、模型对照、部分问答与保存/撤回链路。学术真实性、交互教学有效性、每个图表的逐项数据准确率、用户独立理解、浏览器全部路径、跨论文知识迁移和长期可靠性需要各自额外证据。没有人工全量标注与盲审，就不报告虚假的学术准确率。
