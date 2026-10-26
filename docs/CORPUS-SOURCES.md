# 公开 PDF 测试语料与来源

准备日期：2026-10-24。选取 10 个独立研究/报告，覆盖 AI、通信、人文社科、哲学、经济，实际长度 5–75 页；另有 1 个衍生扫描回归样本。所有文件来自公开作者、出版商、学术机构或 arXiv；未使用付费账户、登录墙或非授权镜像。

搜索采用 agent-reach 的搜索路由；Exa 未配置时使用已连接的 Parallel Search。下载使用 httpx，限制 50 MiB、250 页，检查 `%PDF-` 文件头并实际打开 PDF。网络失败保存在 manifest 的 `download_failures`。

## 可复现运行

```powershell
python scripts/prepare_corpus.py
```

默认复用本地 PDF 并重新计算 hash/页数/文本指标。`--refresh` 会重新下载并更新版本固定信息，远端可变报告可能变化；需要比较原测试时，应先保存现有 manifest 与文件。依赖 `httpx`、`pymupdf`。语料保存在 `data/test-corpus/`，机器可读信息在 `tests/corpus/manifest.json`。

脚本只准备和检查文件，**不调用大模型、OCR、产品 API 或学术核验器**。下表是语料覆盖信息，不是产品通过率。

## 实际下载与可观察结构

| ID / 领域 | 文献与实际页数 | 数字文本字符 / 数字词元 | 图像对象 / 矢量路径 | 图题页 / 表题页 |
|---|---|---:|---:|---|
| `attention` / AI | [Attention Is All You Need](https://arxiv.org/abs/1706.03762) · 2017 · **15 页** | 44,684 / 593 | 3 / 2710 | 3, 4, 13, 14, 15 / 6, 8, 9, 10 |
| `rag` / AI | [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401) · 2020 · **19 页** | 78,885 / 1,036 | 2 / 308 | 2, 7, 8, 17 / 5, 6, 7, 8, 19 |
| `adaptive-dcs-somp` / 通信 | [Adaptive DCS-SOMP for Localization Parameter Estimation in 5G Networks](https://www.mdpi.com/1424-8220/23/22/9073) · 2023 · **12 页** | 66,841 / 772 | 5 / 1641 | 3, 5, 6, 7, 9, 10 / 2, 3, 9, 10, 11 |
| `shannon` / 通信 | [A Mathematical Theory of Communication](https://doi.org/10.1002/j.1538-7305.1948.tb01338.x) · 1948 · **55 页** | 198,951 / 1,473 | 0 / 219 | 2, 4, 8, 9, 10, 11, 21, 22, 23, 25, 27 / 无匹配 |
| `lyrics` / 人文社科 | [Decoding the Style and Bias of Song Lyrics](https://arxiv.org/abs/1907.07818) · 2019 · **5 页** | 29,950 / 302 | 9 / 85 | 2, 3 / 4 |
| `moral-machine` / 哲学/实验伦理/人文社科 | [The Moral Machine experiment](https://dspace.mit.edu/entities/publication/c5779012-d165-4644-b276-76ab3365ca26) · 2018 · **17 页** | 43,094 / 275 | 6 / 98 | 4, 6, 8, 10 / 无匹配 |
| `simulation-argument` / 哲学 | [Are You Living in a Computer Simulation?](https://simulation-argument.com/) · 2003 · **14 页** | 37,690 / 155 | 0 / 25 | 无匹配 / 无匹配 |
| `generative-ai-work` / 经济 | [Generative AI at Work](https://www.nber.org/papers/w31161) · 2023 · **57 页** | 191,134 / 1,719 | 3 / 5517 | 10, 12, 14, 19, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42 / 11, 13, 43, 46, 47 |
| `macroeconomics-ai` / 经济 | [The Simple Macroeconomics of AI](https://www.nber.org/papers/w32487) · 2024 · **58 页** | 178,416 / 1,287 | 1 / 6832 | 39, 40, 42, 43 / 40 |
| `cnnic55` / 人文社科/经济研报 | [第55次中国互联网络发展状况统计报告](https://www.cnnic.cn/n4/2025/0117/c88-11229.html) · 2025 · **75 页** | 98,143 / 3,634 | 280 / 1837 | 16, 17, 18, 19, 20, 21, 23, 24, 25, 27, 28, 29, 30, 31, 32, 34, 35, 38, 39, 40, 42, 43, 44, 46, 47, 50, 51, 53, 56, 58, 59 / 15, 17, 18, 21, 33, 56 |

**解释限制：**图像对象可能是 logo，矢量路径可能是页面装饰。图题/表题来自正则匹配，正文引用、附录和拆行会造成漏检/误检。数字词元包括页码和参考文献。这里没有证明图表已被正确理解、表格已准确抽取或数字已通过学术核验。`get_text(sort=True)` 也不能证明双栏顺序正确。

理论哲学 `simulation-argument` 是有意保留的无实证图表反例：它包含概率表达与条件论证，却没有实验数据。应测试系统能否选择论证关系与条件展开，避免为统一模板强造数据图或“实验结果”。其余语料包含图题、表题、绘图或实际数据线索；不能据此保证所有线索都属于有效图表。

## 每篇的重点测试边界

### Attention Is All You Need

作者：Ashish Vaswani；Noam Shazeer；Niki Parmar；Jakob Uszkoreit；Llion Jones；Aidan N. Gomez；Łukasz Kaiser；Illia Polosukhin。
版本：arXiv v7。
实际下载入口：https://arxiv.org/pdf/1706.03762v7
SHA-256：`bdfaa68d8984f0dc02beaca527b76f207d99b666d31d1da728ee0728182df697`。

双栏阅读顺序；注意力公式/矩阵维度；BLEU表格与训练设置；机制演示不冒充训练复现。

### Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks

作者：Patrick Lewis；Ethan Perez；Aleksandra Piktus；Fabio Petroni；Vladimir Karpukhin；Naman Goyal；Heinrich Küttler；Mike Lewis；Wen-tau Yih；Tim Rocktäschel；Sebastian Riedel；Douwe Kiela。
版本：arXiv v4。
实际下载入口：https://arxiv.org/pdf/2005.11401v4
SHA-256：`23e3249e9a1e75418d82efecab0ea8c4d033b89c93742f63208d47ce01f21233`。

概率分解与检索生成关系；主文与附录区分；跨论文概念复用；检索准确不等于生成事实正确。

### Adaptive DCS-SOMP for Localization Parameter Estimation in 5G Networks

作者：Paulo Francisco da Conceição；Flávio Geraldo Coelho Rocha。
版本：publisher v2 if available; actual download_url and hash authoritative。
实际下载入口：https://mdpi-res.com/d_attachment/sensors/sensors-23-09073/article_deploy/sensors-23-09073-v2.pdf
SHA-256：`b4deafe808239771e804f2b655156d09b5711ee2e3fc361a06066b673115de77`。

稀疏恢复与通信前置知识；多层公式和符号；仿真曲线不等于真实部署；搜索域教学模型的边界。

### A Mathematical Theory of Communication

作者：Claude E. Shannon。
版本：Harvard institutional reprint with corrections, combines July/October 1948 installments。
实际下载入口：https://people.math.harvard.edu/~ctm/home/text/others/shannon/entropy/entropy.pdf
SHA-256：`6e4e3411984f3edf99dbfe8b941cb5e8a321379ff0cae6ae5c1f592ad8882ca8`。

长理论文档覆盖；定理与条件不可省略；熵公式与示意图；历史语境与后续知识分开。

### Decoding the Style and Bias of Song Lyrics

作者：Manash Pratim Barman；Amit Awekar；Sambhav Kothari。
版本：arXiv v1。
实际下载入口：https://arxiv.org/pdf/1907.07818v1
SHA-256：`66fe209b72eb93c6423a5c183ce4ae091f6e857e32804a277391698df6b5b283`。

数字人文与文化语料；WEAT偏差指标；表格统计不能替代社会因果结论；短文完整论证。

### The Moral Machine experiment

作者：Edmond Awad；Sohan Dsouza；Richard Kim；Jonathan Schulz；Joseph Henrich；Azim Shariff；Jean-François Bonnefon；Iyad Rahwan。
版本：MIT author final manuscript; not publisher layout。
实际下载入口：https://dspace.mit.edu/server/api/core/bitstreams/750c4524-46a2-4013-916a-c8131d726b56/content
SHA-256：`59c4f6158add045bb3fbd85d9f7d4f61305583ad1441523759a88590efccf5fb`。

图示情景与偏好统计；描述性伦理不等于规范性结论；文化聚类与样本选择；人数/决策次数/地域单位区别。

### Are You Living in a Computer Simulation?

作者：Nick Bostrom。
版本：author-hosted paper published in Philosophical Quarterly 53(211):243–255。
实际下载入口：http://simulation-argument.com/simulation.pdf
SHA-256：`be823e12764a35cdd6b36d8db0d5047eebeb2d3137801f5524cd84f1d4f297de`。

纯理论哲学论证结构；三分命题不能误写成已证实生活在模拟中；概率公式的前提；没有实证图表时不得强造数值演示。

### Generative AI at Work

作者：Erik Brynjolfsson；Danielle Li；Lindsey R. Raymond。
版本：NBER working paper or arXiv 2304.11771 v1 fallback; actual download_url authoritative; not 2025 QJE version。
实际下载入口：https://arxiv.org/pdf/2304.11771v1
SHA-256：`ac0a4e183aa6f9360d201b454c06d8077400bae6be84851574eb0f4369a6430d`。

长实证论文与附录；样本人数版本差异5179/5172；平均效果与异质性；相关性/因果识别与外推边界。

### The Simple Macroeconomics of AI

作者：Daron Acemoglu。
版本：NBER working paper or May 12 2024 MIT author-hosted fallback; actual download_url authoritative。
实际下载入口：https://shapingwork.mit.edu/wp-content/uploads/2024/05/Acemoglu_Macroeconomics-of-AI_May-2024.pdf
SHA-256：`b0183405d850db11dcce0ff1e82cbc217175835032497776852d6afce49b8767`。

长理论加数据校准；模型假设与预测区间；GDP与TFP及时间尺度；与微观生产率研究比较不能直接等同。

### 第55次中国互联网络发展状况统计报告

作者：中国互联网络信息中心（CNNIC）。
版本：official January 2025 report, data through December 2024。
实际下载入口：https://www.cnnic.cn/NMediaFile/2025/0428/MAIN17458061595875K4FP1NEUO.pdf
SHA-256：`d20a33e7eb892f38245c5773919cbec4c86e0671f601b9c9acb15e7b66278c5e`。

中文长研报与目录页码；图表单位亿/万/百分比；统计时点及地域口径；描述性数据不可伪造因果关系。

## 版本与来源回查的关键陷阱

- `generative-ai-work`：NBER 入口出现 TLS/403，改用 Stanford 作者机构页面明确链接的 arXiv v1 原始预印本。下载文件有 57 页，全文 `5,179` 出现 3 次，`5,172` 为 0。2025 QJE 版本/更新摘要使用 5,172 和不同效果估计；回答不得把外部新版本的数字当作上传 PDF 的内容。版本区别的来源：[Stanford SIEPR 2023 摘要](https://siepr.stanford.edu/publications/working-paper/generative-ai-work)、[Stanford 2025 期刊版](https://www.gsb.stanford.edu/faculty-research/publications/generative-ai-work)。
- `macroeconomics-ai`：NBER 和 economics.mit.edu 入口失败后，使用 MIT Shaping the Future of Work 的 May 2024 作者稿（含机构封面，共 58 页），不是 2024-10 期刊排版版。不同日期的稿件上界估计存在变化，不能跨版本拼数。
- `moral-machine`：MIT 作者终稿，不是 Nature 6 页版式。PDF 中前置机构封面和正文题名与正式发表题名不完全相同。稳定下载入口使用 DSpace content API，避免保存会过期的重定向 CDN 签名 URL。
- `shannon`：Harvard 教师学术目录托管的校订重排版，合并了 1948 年七月和十月两部分；PDF 的 55 页不能当作期刊原始页码。
- `cnnic55`：2025 年 1 月发布，统计截至 2024 年 12 月；目录编号、印刷页码与 PDF 页序可能不同。旧报告不可被当前联网数据静默覆盖。
- `simulation-argument`：HTTPS 握手失败后使用作者站公开 HTTP 入口（服务可能再重定向），未绕过登录或付费限制；SHA-256 固定实际文件。

## OCR 专用衍生样本

`data/test-corpus/attention-page3-scan.pdf` 将 `attention` 的 PDF 第 3 页以 2× 渲染栅格化，再写入新的一页 PDF。它不是新论文，也不是天然扫描质量的代表。无数字文本层，应触发 OCR 路径；可以与来源页比对文字、公式和图示。它只能验证“纯图页能否进入 OCR”，不能代表旋转、低清、手写、中文扫描、复杂扫描表格等场景。

## 建议的实际产品测试口径

1. 每篇独立上传，检查正确文件、标题/版本、页数、任务终态、失败/未完整标记，不能只检查 HTTP 200。
2. 检查首轮完整论证、条件和限制是否覆盖；长文附录是否漏失，以及末页/末节内容是否真正参与生成。
3. 从至少一个图题、表题或公式入口提问，回查原 PDF 页序与可定位片段。理论哲学改用前提—推理—结论，禁止捏造实验。
4. 对重要数值抽样，核对分母、单位、统计时点、版本、置信区间与因果措辞；不以“引用存在”认定引用支持结论。
5. 请求外部知识与学术核验，区分原文、权威补充、教学假设，记录检索命中/失败，检查访问不到全文时有无降级说明。
6. 对话操作已有演示，检查参数范围、工具回执、解释一致性与撤回；教学演示不能声称复现论文数值。
7. 保存概念后换一篇文献，检查只跳过已保存知识层，仍解释新定义、条件和新用途；不加入则应再次解释。
8. 连续对话、位置锚点、跨文献比较、补充预览/应用/撤回和独立概念保存分别记录结果。

本页不替代实际产品边界测试报告。真实模型/联网/OCR的成功率、延迟、费用和学术判断需要在产品完成接入后按调用证据另行报告。
