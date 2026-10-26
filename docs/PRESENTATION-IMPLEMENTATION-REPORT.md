# 交互讲解呈现实测记录

快照：2026-10-25T05:17:15+08:00。报告由 `python scripts/report_presentations.py` 读取原始产物生成，不调用模型。

各批先完整运行、记录问题，再集中修复；不同批次不覆盖原始结果。tested只表示流程结束，不表示每幅图解通过；validated表示结构、实际浏览器操作、视觉模型和来源模型检查通过。模型检查不是人工学术认证。

## 阶段A：独立呈现链路

独立SQLite表、任务与版本、正文/来源哈希绑定、HTML/SVG清理、可信状态运行器、iframe隔离、宿主来源/概念/选区/步骤桥接已接入。原正文、对话、概念库和页面补充不由呈现任务写入。

首轮30项后端测试通过；构建与原教学浏览器7组通过；合成2状态图解真实操作通过。合成材料只证明运行器基础，不算真实文献呈现成功。原始记录：`artifacts/presentation-phase-a/`。

## 固定版本批次

| 批次 | 材料 | 流程 | 通过/阻断场景 | 正文及用户内容不变 | 耗时秒 |
|---|---|---|---|---|---|
| cross-domain-first | adaptive-dcs-somp | tested | 1/2 | True | 750.98 |
| cross-domain-first | attention | tested | 0/3 | True | 265.92 |
| cross-domain-first | cnnic55 | tested | 0/3 | True | 644.98 |
| cross-domain-first | generative-ai-work | tested | 0/3 | True | 552.02 |
| cross-domain-first | lyrics | failed | 0/0 | True | 409.72 |
| cross-domain-first | macroeconomics-ai | tested | 0/3 | True | 528.2 |
| cross-domain-first | moral-machine | tested | 1/2 | True | 597.83 |
| cross-domain-first | rag | tested | 0/3 | True | 639.58 |
| cross-domain-first | shannon | tested | 1/2 | True | 434.97 |
| cross-domain-first | simulation-argument | tested | 1/2 | True | 220.38 |
| cross-domain-retest | adaptive-dcs-somp | tested | 2/1 | True | 213.62 |
| cross-domain-retest | attention | tested | 2/1 | True | 475.67 |
| cross-domain-retest | cnnic55 | tested | 2/1 | True | 1411.93 |
| cross-domain-retest | generative-ai-work | tested | 2/1 | True | 1389.14 |
| cross-domain-retest | lyrics | tested | 1/2 | True | 829.59 |
| cross-domain-retest | macroeconomics-ai | tested | 3/0 | True | 1325.22 |
| cross-domain-retest | cnnic55 | None | 待定/待定 | 待定 | 未结束 |
| cross-domain-retest | moral-machine | tested | 3/0 | True | 548.31 |
| cross-domain-retest | rag | tested | 2/1 | True | 545.45 |
| cross-domain-retest | shannon | tested | 3/0 | True | 732.66 |
| cross-domain-retest | simulation-argument | tested | 2/1 | True | 1576.94 |
| release | adaptive-dcs-somp | tested | 3/0 | True | 234.58 |
| release | attention | tested | 2/1 | True | 128.66 |
| release | cnnic55 | tested | 3/0 | True | 262.72 |
| release | generative-ai-work | tested | 2/1 | True | 343.16 |
| release | lyrics | tested | 2/1 | True | 288.77 |
| release | macroeconomics-ai | tested | 3/0 | True | 220.81 |
| release | moral-machine | tested | 3/0 | True | 262.41 |
| release | rag | tested | 3/0 | True | 124.42 |
| release | shannon | tested | 3/0 | True | 229.06 |
| release | simulation-argument | tested | 3/0 | True | 273.98 |
| release-candidate | adaptive-dcs-somp | tested | 2/1 | True | 267.48 |
| release-candidate | attention | tested | 1/2 | True | 657.08 |
| release-candidate | cnnic55 | tested | 3/0 | True | 666.89 |
| release-candidate | generative-ai-work | tested | 1/2 | True | 531.91 |
| release-candidate | lyrics | tested | 0/3 | True | 546.09 |
| release-candidate | macroeconomics-ai | tested | 3/0 | True | 496.31 |
| release-candidate | moral-machine | tested | 1/2 | True | 499.19 |
| release-candidate | rag | tested | 3/0 | True | 282.12 |
| release-candidate | shannon | tested | 3/0 | True | 449.2 |
| release-candidate | simulation-argument | tested | 2/1 | True | 656.98 |
| release-verification | adaptive-dcs-somp | tested | 3/0 | True | 234.58 |
| release-verification | attention | tested | 2/1 | True | 128.66 |
| release-verification | cnnic55 | tested | 3/0 | True | 262.72 |
| release-verification | generative-ai-work | tested | 2/1 | True | 343.16 |
| release-verification | lyrics | tested | 2/1 | True | 288.77 |
| release-verification | macroeconomics-ai | tested | 3/0 | True | 220.81 |
| release-verification | moral-machine | tested | 3/0 | True | 262.41 |
| release-verification | rag | tested | 3/0 | True | 124.42 |
| release-verification | shannon | tested | 3/0 | True | 229.06 |
| release-verification | simulation-argument | tested | 3/0 | True | 273.98 |
| representative-first | attention | tested | 2/1 | True | 235.33 |
| representative-first | cnnic55 | tested | 1/2 | True | 506.55 |
| representative-first | simulation-argument | tested | 1/2 | True | 202.23 |
| representative-retest | attention | tested | 2/1 | True | 198.39 |
| representative-retest | cnnic55 | tested | 1/2 | True | 622.81 |
| representative-retest | simulation-argument | tested | 3/0 | True | 219.72 |

中断恢复的批次另存 interruption 记录；duration_includes_interruption=true 的耗时包含中断，不能当作正常冷启动速度。代码/提示词冻结哈希以各批 implementation.json 为准。


## 各批实际宿主浏览器检查

- cross-domain-first / attention：issues；可用图解0；各图解状态变化[]。
- cross-domain-first / rag：issues；可用图解0；各图解状态变化[]。
- cross-domain-first / adaptive-dcs-somp：passed；可用图解1；各图解状态变化[{"id": "scene-240699c377a99039450c", "states": 3, "distinct_graphics": 3}]。
- cross-domain-first / shannon：passed；可用图解1；各图解状态变化[{"id": "scene-3c618bcbcfe4b965cf06", "states": 3, "distinct_graphics": 3}]。
- cross-domain-first / lyrics：issues；可用图解0；各图解状态变化[]。
- cross-domain-first / moral-machine：passed；可用图解1；各图解状态变化[{"id": "scene-05e84098f62710dd5f5e", "states": 3, "distinct_graphics": 3}]。
- cross-domain-first / simulation-argument：passed；可用图解1；各图解状态变化[{"id": "scene-9248f54060c71ecad2f4", "states": 3, "distinct_graphics": 3}]。
- cross-domain-first / generative-ai-work：issues；可用图解0；各图解状态变化[]。
- cross-domain-first / macroeconomics-ai：issues；可用图解0；各图解状态变化[]。
- cross-domain-first / cnnic55：issues；可用图解0；各图解状态变化[]。
- cross-domain-retest / attention：passed；可用图解2；各图解状态变化[{"id": "scene-3774984c7c2f1bb100ce", "states": 4, "distinct_graphics": 4}, {"id": "scene-82a293db8221c2260d2d", "states": 3, "distinct_graphics": 3}]。
- cross-domain-retest / rag：passed；可用图解2；各图解状态变化[{"id": "scene-7b05266bd91d8851ccb3", "states": 3, "distinct_graphics": 3}, {"id": "scene-152dac77549c477be25e", "states": 3, "distinct_graphics": 3}]。
- cross-domain-retest / adaptive-dcs-somp：passed；可用图解2；各图解状态变化[{"id": "scene-831a210ec766e5b1a099", "states": 3, "distinct_graphics": 3}, {"id": "scene-4ce4fbcef461b9e0d150", "states": 3, "distinct_graphics": 3}]。
- cross-domain-retest / shannon：passed；可用图解3；各图解状态变化[{"id": "scene-cca6ca08bd63b188bebc", "states": 3, "distinct_graphics": 3}, {"id": "scene-9582cf6dffe7b158f856", "states": 4, "distinct_graphics": 4}, {"id": "scene-424b9d734dc4a583dd24", "states": 3, "distinct_graphics": 3}]。
- cross-domain-retest / lyrics：passed；可用图解1；各图解状态变化[{"id": "scene-ce678bc978ca58984368", "states": 2, "distinct_graphics": 2}]。
- cross-domain-retest / moral-machine：passed；可用图解3；各图解状态变化[{"id": "scene-95ac0ee34f2a7d775a3d", "states": 4, "distinct_graphics": 4}, {"id": "scene-6b75f118cf7eac27ee5e", "states": 4, "distinct_graphics": 4}, {"id": "scene-0f7e715d8ca3753c4aa8", "states": 3, "distinct_graphics": 3}]。
- cross-domain-retest / simulation-argument：passed；可用图解2；各图解状态变化[{"id": "scene-effdf5f83198524b7d2a", "states": 3, "distinct_graphics": 3}, {"id": "scene-4be7feabae97b214d24a", "states": 3, "distinct_graphics": 3}]。
- cross-domain-retest / generative-ai-work：passed；可用图解2；各图解状态变化[{"id": "scene-91511634b01721e4029b", "states": 4, "distinct_graphics": 3}, {"id": "scene-c55a0288f8acaf79eefc", "states": 2, "distinct_graphics": 2}]。
- cross-domain-retest / macroeconomics-ai：passed；可用图解3；各图解状态变化[{"id": "scene-ef1f1abb7b796d3773fd", "states": 3, "distinct_graphics": 3}, {"id": "scene-25fbdd3ff573fa7dab71", "states": 3, "distinct_graphics": 3}, {"id": "scene-5a1a07901e824a581e79", "states": 3, "distinct_graphics": 3}]。
- cross-domain-retest / cnnic55：passed；可用图解2；各图解状态变化[{"id": "scene-aa51edd0386e636a377d", "states": 4, "distinct_graphics": 4}, {"id": "scene-1b969ff6410269f7030c", "states": 3, "distinct_graphics": 3}]。
- release-candidate / attention：passed；可用图解1；各图解状态变化[{"id": "scene-a3089562a4575f566b2b", "states": 3, "distinct_graphics": 3}]。
- release-candidate / rag：passed；可用图解3；各图解状态变化[{"id": "scene-01dbd7e477a31fe28ba8", "states": 3, "distinct_graphics": 3}, {"id": "scene-36860b5101b051e5ac36", "states": 2, "distinct_graphics": 2}, {"id": "scene-e4ab0bf24ff2db8b9aa0", "states": 3, "distinct_graphics": 3}]。
- release-candidate / adaptive-dcs-somp：passed；可用图解2；各图解状态变化[{"id": "scene-235a00064c1c58339401", "states": 2, "distinct_graphics": 2}, {"id": "scene-ac2881321d35c943243e", "states": 3, "distinct_graphics": 3}]。
- release-candidate / shannon：passed；可用图解3；各图解状态变化[{"id": "scene-8ab37ab5688976ab39f1", "states": 3, "distinct_graphics": 3}, {"id": "scene-0ca6cb3b96355ea528fd", "states": 4, "distinct_graphics": 4}, {"id": "scene-5de0c59f83428cdb1c85", "states": 3, "distinct_graphics": 3}]。
- release-candidate / lyrics：issues；可用图解0；各图解状态变化[]。
- release-candidate / moral-machine：passed；可用图解1；各图解状态变化[{"id": "scene-dee607c6e69be89709fa", "states": 4, "distinct_graphics": 4}]。
- release-candidate / simulation-argument：passed；可用图解2；各图解状态变化[{"id": "scene-7479a2a0152331ba666f", "states": 3, "distinct_graphics": 3}, {"id": "scene-7adc010e81065f6c01b7", "states": 3, "distinct_graphics": 3}]。
- release-candidate / generative-ai-work：passed；可用图解1；各图解状态变化[{"id": "scene-60e81cdf4c1f964048fe", "states": 3, "distinct_graphics": 3}]。
- release-candidate / macroeconomics-ai：passed；可用图解3；各图解状态变化[{"id": "scene-f50760131ee6c2b09c33", "states": 3, "distinct_graphics": 3}, {"id": "scene-9e639eb072693384e7b5", "states": 3, "distinct_graphics": 3}, {"id": "scene-85732ea86e1792bb3a0f", "states": 3, "distinct_graphics": 3}]。
- release-candidate / cnnic55：passed；可用图解3；各图解状态变化[{"id": "scene-792b5fa822d54b23645b", "states": 4, "distinct_graphics": 4}, {"id": "scene-efa065bfa9840133b5c4", "states": 3, "distinct_graphics": 3}, {"id": "scene-10eb8177e222b733195f", "states": 3, "distinct_graphics": 3}]。
- release-verification / attention：issues；可用图解2；各图解状态变化[{"id": "scene-caa5e699544c8d1383ac", "states": 4, "distinct_graphics": 4}, {"id": "scene-333b6a3d769e72e8c155", "states": 3, "distinct_graphics": 3}]。
- release-verification / rag：issues；可用图解3；各图解状态变化[{"id": "scene-52a7469f50b9f9d359fb", "states": 3, "distinct_graphics": 3}, {"id": "scene-2b50c5384109fffaaf5b", "states": 2, "distinct_graphics": 2}, {"id": "scene-a6ab1bdecc45db83d3f3", "states": 3, "distinct_graphics": 3}]。
- release-verification / adaptive-dcs-somp：issues；可用图解3；各图解状态变化[{"id": "scene-476a0fd37d6f0024b83b", "states": 3, "distinct_graphics": 3}, {"id": "scene-2ffa5f89c893c244c49f", "states": 2, "distinct_graphics": 2}, {"id": "scene-265b926d3d35b08f49cd", "states": 3, "distinct_graphics": 3}]。
- release-verification / shannon：issues；可用图解3；各图解状态变化[{"id": "scene-fcd6154a4797aafb84e6", "states": 3, "distinct_graphics": 3}, {"id": "scene-e0e8b3bf9315ccc0a691", "states": 4, "distinct_graphics": 4}, {"id": "scene-fbca1904647a280684a2", "states": 3, "distinct_graphics": 3}]。
- release-verification / lyrics：issues；可用图解2；各图解状态变化[{"id": "scene-01228f078b48548ac91c", "states": 2, "distinct_graphics": 2}, {"id": "scene-602abd507a6cae93e60c", "states": 3, "distinct_graphics": 3}]。
- release-verification / moral-machine：issues；可用图解3；各图解状态变化[{"id": "scene-73c302a57e110000f2e2", "states": 4, "distinct_graphics": 4}, {"id": "scene-ec00166c186d732b4eb0", "states": 4, "distinct_graphics": 4}, {"id": "scene-a137f99c13ae0a4f22cf", "states": 3, "distinct_graphics": 3}]。
- release-verification / simulation-argument：issues；可用图解3；各图解状态变化[{"id": "scene-15dafa4887b8b9e42957", "states": 3, "distinct_graphics": 3}, {"id": "scene-d811d17a94e8e4152244", "states": 3, "distinct_graphics": 3}, {"id": "scene-ca8f055fbbfea137c12c", "states": 3, "distinct_graphics": 3}]。
- release-verification / generative-ai-work：issues；可用图解2；各图解状态变化[{"id": "scene-7ef40af1abcf72ba93de", "states": 4, "distinct_graphics": 3}, {"id": "scene-7ee81246edbafe01968d", "states": 2, "distinct_graphics": 2}]。
- release-verification / macroeconomics-ai：passed；可用图解3；各图解状态变化[{"id": "scene-76fc131c429460c2ef14", "states": 3, "distinct_graphics": 3}, {"id": "scene-6ed23d1e3b0cb25dec37", "states": 3, "distinct_graphics": 3}, {"id": "scene-163f83516131ceaae074", "states": 3, "distinct_graphics": 3}]。
- release-verification / cnnic55：issues；可用图解3；各图解状态变化[{"id": "scene-3bad18d0974a77c0e866", "states": 4, "distinct_graphics": 4}, {"id": "scene-3834e53e36c15b348f13", "states": 3, "distinct_graphics": 3}, {"id": "scene-ccce59c489719caaedba", "states": 3, "distinct_graphics": 3}]。
- representative-first / attention：issues；可用图解2；各图解状态变化[{"id": "scene-907a959d25daaf5629ea", "states": 4, "distinct_graphics": 4}, {"id": "scene-03e37dea5a767159abc5", "states": 3, "distinct_graphics": 3}]。
- representative-first / simulation-argument：issues；可用图解1；各图解状态变化[{"id": "scene-73e2591378832aee4f3b", "states": 3, "distinct_graphics": 3}]。
- representative-first / cnnic55：passed；可用图解1；各图解状态变化[{"id": "scene-aca7e9ac9f36a4798e5e", "states": 3, "distinct_graphics": 3}]。
- representative-retest / attention：passed；可用图解2；各图解状态变化[{"id": "scene-d20b222b20148be7303c", "states": 4, "distinct_graphics": 4}, {"id": "scene-6b558f24cd2637ee19f5", "states": 3, "distinct_graphics": 3}]。
- representative-retest / simulation-argument：passed；可用图解3；各图解状态变化[{"id": "scene-0925cf9ef8eaa5237778", "states": 3, "distinct_graphics": 3}, {"id": "scene-8a4eb7e59f45afedeaff", "states": 3, "distinct_graphics": 3}, {"id": "scene-653c939243965f8ed14e", "states": 3, "distinct_graphics": 3}]。
- representative-retest / cnnic55：failed；可用图解2；各图解状态变化[{"id": "scene-327afe0426a14202a1d5", "states": 3, "distinct_graphics": 3}]。

## 可见图形与数据操作追加审计

追加检查过滤隐藏元素，比较可见形状的几何、变换与实际样式，以及数字标签/数据行；检查每个状态是否有不同的可观察结果。包括被管线阻断但仍可渲染的候选。操作通过不能替代布局和事实通过。

- cross-domain-retest：{"passed": 28, "issues": 0, "failed": 0, "unavailable": 2}；状态总数88。
- release-candidate：{"passed": 28, "issues": 0, "failed": 0, "unavailable": 2}；状态总数86。
- release-verification：{"passed": 30, "issues": 0, "failed": 0, "unavailable": 0}；状态总数93。

## 人工抽查发现的漏检

- cross-domain-retest / cnnic55 / commerce_payment_logistics：Trusted emphasis style changes originally white text to blue on dark fill; pipeline visual gate did not block this. {"label": "政策驱动：消费品以旧换新 & 通用航空装备创新", "fill": "rgb(49, 92, 200)", "background": "rgb(38, 54, 75)", "font_size": "12px", "group_class": "pm-emphasis", "contrast_ratio": 2.04}
- cross-domain-retest / cnnic55 / commerce_payment_logistics：Lower-bound qualifier 超 is omitted in chart and initial-state explanation; source model returned supported.

人工问题独立于管线计数。管线validated不等于已发布；追加检查或人工抽查发现问题的候选仍需修复和重新验收。


## 保留的问题记录

- **cross-domain-first / adaptive-dcs-somp / sensing-matrix-construction**：呈现包含不允许的标签：sub
- **cross-domain-first / adaptive-dcs-somp / adaptive-mechanism**：呈现包含不允许的标签：sub
- **cross-domain-first / attention / problem-statement**：图解视觉复核待处理：图中三条曲线（O(n), O(log n), O(1)）在纵轴‘操作步数 / 路径长度’下被绘制于同一坐标系，但O(1)是常量、O(log n)是对数增长、O(n)是线性增长，三者量纲虽同为‘步数’，但数值尺度差异巨大（例如n=1000时，O(n)=1000, O(log n)≈10, O(1)=1），直接在同一图上用相同纵轴刻度绘制会严重压缩O(log n)与O(1)的视觉表现，易误导读者认为O(log n)与O(1)接近；图中O(1)线被绘为水平线（合理），但O(log n)虚线斜率明显偏大（视觉上接近线性），与理论log增长不符，存在图形失真风险。；标签可读性：各状态图中注释框文字（如‘RNN / LSTM’、‘Transformer’）与曲线端点标注（O(n), O(log n), O(1)）位置重叠或紧邻，尤其在state-rnn和state-transformer中，O(n)红点与注释框边界几乎相切，存在轻微视觉干扰；但未达到‘严重重叠’程度，仍可辨识。；横纵轴标注清晰，无错别字；但‘理论最大路径长度随序列长度 n 的变化趋势（基于 Table 1 数据）’这一说明未在图中体现Table 1内容，属外部依赖，不影响当前图解可读性判断。；关键矛盾：state-rnn图中将CNN标注为‘距离增长’，但图中O(log n)曲线被归于CNN（见state-cnn文本），而state-rnn图中该曲线无明确归属标签，仅靠上下文推断；且state-rnn图中O(log n)虚线起点非原点（有y轴截距），与理论log(n)在n→1时趋近0不符，暗示绘图未严格按理论函数绘制，削弱了‘关系可辨’的可靠性。
- **cross-domain-first / attention / multi-head-attention**：图解视觉复核待处理：图中 'd_k=64' 与 'd_k = d_model/h' 两种标注并存于不同状态，但未明确说明 d_model 值（如 d_model=512），无法验证一致性；PDF原文图2右侧虽有结构示意，但未标具体数值，故无法确认是否矛盾。；图中 'Concat' 箭头指向 'W^O' 模块，但未标明 Concat 输出维度（应为 h × d_k = d_model），而 W^O 输入维度需匹配该值；PDF原文公式(1)显示输出为 d_model 维，但图中未显式体现维度守恒，存在潜在量纲隐含假设风险。；各状态图中 'Head 1' 至 'Head h' 为垂直排列示意，并行计算关系依赖文字描述（'并行处理后合并'），图形本身未用并行连线/分组框等视觉元素明确表达‘并行’，仅靠文本提示，关系可辨性弱。；标签 'Q,K,V' 与 'd_model' 共置一框，易误读为 Q/K/V 各自维度为 d_model；实际应为三者拼接或分别投影前的输入张量维度为 (seq_len, d_model)，但图中未区分 Q/K/V 是否已分离或共享输入，存在歧义。
- **cross-domain-first / attention / mt-results**：图解视觉复核待处理：图中柱状图将BLEU分数（无量纲性能指标）与训练成本（FLOPs，计算量）混排在同一坐标系下，但Y轴仅标注'BLEU 分数'，未明确区分不同量纲数据；尽管文字说明'EN-FR 训练成本 (FLOPs) 对数标度示意'，但图形本身未用双Y轴、不同颜色/样式或分组清晰隔离两类数据，易导致误读为同一量纲比较。；图例说明'■ Transformer (big) | ■ 此前最佳集成模型 | ■ 英法任务结果'存在歧义：三个项目均用相同方块符号（■），未通过颜色/填充差异区分；而实际图中Transformer为蓝色实心，其余为浅粉色，与图例文字描述不一致，造成符号-内容映射错误。；图中'26.30'、'26.36'、'28.4'数值位置紧邻对应模型标签，但未明确标注是EN-DE还是EN-FR任务的BLEU分数；结合文本'EN-DE 41.8 41.0 Transformer (big)'可知28.4应为EN-DE结果，但图表本身缺乏任务标识，需依赖外部文本推断，违反自解释原则。；文字说明'EN-FR 训练成本 (FLOPs) 对数标度示意 1.1·10²¹ 2.3·10¹⁹'，但图中未显示任何对应于该成本值的视觉元素（如第二组柱子或标记），仅在下方文字提及，图形未体现该对比，导致'示意'未在图中可视化呈现。
- **cross-domain-first / cnnic55 / exec_summary_key_metrics**：图解视觉复核待处理：标签可读性：图中‘增长 1608 万人’标注线指向2023.12与2024.12两柱之间，但数值1608万是差值（11.08亿 - 10.92亿 = 0.16亿 = 1600万），实际应为1600万人；截图文字写‘1608万人’，与计算结果存在8万人偏差，属数据不一致，需核验原始报告是否确为1608万（如含四舍五入或统计口径调整）。此属‘DOM准确文字’与图表隐含计算矛盾，影响读图准确性。；量纲混淆风险：左轴标注‘网民规模（亿人/万人）’并用‘亿’单位（10.92亿、11.08亿），右轴为百分比（99.7%、77.5%→78.6%），但图表将三类指标（绝对规模、结构占比、普及率）并置于同一视觉区域且无明确分轴标识（仅靠文字说明‘左轴…右轴…’），易导致读者误将柱高直接比较（如误以为11.08亿与99.7%同量级）。虽有文字说明，但图形本身未通过坐标轴分隔或颜色/样式隔离实现‘操作后关系可辨’，构成视觉误导风险。；图形元素缺失关键标尺：‘互联网普及率 (%)’使用离散柱状图展示两年数据，但未标注Y轴刻度范围（如75%–80%），也未在图中体现‘1.1个百分点’的增量长度比例，仅靠外部文字标注‘提升1.1个百分点’，无法从图形本身直观判断增幅大小，削弱‘操作后关系可辨’要求。；手机网民占比环形图标注歧义：环形图中心显示‘99.7%’，外圈标注‘规模 11.05 亿人’，但11.05亿 ≠ 11.08亿（总网民规模），暗示手机网民规模=99.7%×11.08亿≈11.05亿，计算合理；然而图中未明确说明该‘11.05亿’是推算值还是独立统计值，且与左侧柱图‘11.08亿’未建立显式关联线或注释，易引发‘不同量纲直接比较’误解（如误将11.05亿与11.08亿视为独立指标而非子集关系）。；时点标注不一致：网民规模柱图标注为‘2023.12’和‘2024.12’，而普及率柱图标注为‘2023’和‘2024’，未明确是否同为12月数据；若非，则跨年比较存在时间错位风险，影响‘两个明确时点’的严谨性。
- **cross-domain-first / cnnic55 / infra_resources_ipv6_5g**：图解视觉复核待处理：Y轴标签‘数值/占比’模糊，未区分不同指标的量纲（IPv6地址单位为‘块/32’，5G基站为‘万个’，占比为百分比），存在将不同量纲数据置于同一坐标系暗示可直接比较的风险。；第一张图（IPv6地址趋势）中，2024年数据标注为‘69148 块/32’，但图表X轴为年份、Y轴为‘数值/占比’，未明确该数值是绝对数量还是占比；结合文字说明‘2024年达到69148块/32’，应为绝对数量，但Y轴无单位标注，易致误读。；第二张图（5G基站）中，柱状图高度对应‘数值/占比’，但2024年标注‘33.2% 占比’，而下方文字说明‘2024年11月总数419.1万个，占比33.2%’，表明33.2%是占比，419.1万是绝对数；图中仅标出占比，未体现绝对数量，且柱高若按占比绘制，则与2020–2023年柱高逻辑不一致（因早期占比远低于33.2%，但柱高增长显著），暗示图表可能混用绝对数与占比作高度依据，导致量纲混淆。；两图共享同一图注‘图：2020-2024年关键基础设施指标变化示意’，但实际展示的是不同指标、不同时间截点（12月 vs 11月）、不同量纲数据，未在图内或图注中清晰分离，违反可视化一致性原则。；‘注意：部分数据截至11月 非全年同比’提示存在时间口径不一致问题，但图表未以视觉方式（如虚线、颜色区分、标注具体月份）标示各数据点实际截止时间，影响操作后关系辨识（例如2024年IPv6数据为12月，5G为11月，无法判断是否同期可比）。
- **cross-domain-first / cnnic55 / commerce_payment_logistics**：原步骤映射不完整
- **cross-domain-first / generative-ai-work / main_productivity_result**：图解视觉复核待处理：图A中'Pre AI'与'Post AI'曲线在截图中严重重叠，标签（如'Res/Hr'轴、'密度'轴）虽存在但分辨率低，无法确认是否可读或存在严重视觉遮挡；原PDF页（Figure 3）显示清晰多子图，但当前两状态截图未完整呈现该图，仅局部示意，无法验证'右移'结论的图形依据是否充分。；图B机制分解部分：state-dist中'处理时长 (AHT) 14'与'并行对话数 (CPH) 14'数值相同且无单位/方向标识，易误判为绝对值而非变化率；state-event中修正为'-9%'与'+14%'，表明原状态文字存在歧义，但截图未显示百分号或符号，仅靠文本描述无法确认图形本身是否标注了正负号或%符号，存在读图歧义风险。；质量指标中'solve rate: 1.3'在state-dist中无单位，在state-event中为'+1.3 pp'，但截图中未显示'pp'字样，若图形实际未标注单位，则可能误导读者以为是倍数或比例（如1.3倍），构成量纲混淆风险；需依赖原文图表确认是否明确标为'percentage points'。；两状态截图均缺失Figure 3完整结构（如子图B–E），仅展示A与部分B；而原PDF页（image 3）显示Figure 3含5个子图（A–E），当前截图无法验证各子图坐标轴量纲是否统一（例如：A为Res/Hr，B为秒/分钟，C为Calls/Hr，D为无量纲比率，E为百分比），因此无法判断是否存在‘不同量纲直接比较’的图形设计问题。
- **cross-domain-first / generative-ai-work / heterogeneity_skill**：状态操作目标不存在：quality-note
- **cross-domain-first / generative-ai-work / experience_curve**：图解视觉复核待处理：标签可读性：图中曲线标签（如 'Never', 'Always', 'Treated'）在截图中部分被截断或模糊（例如第一张图中 'Never' 右侧被截，第二张图中 'Treated' 与 'Never' 重叠），影响准确识别；第三张PDF原页图例清晰（'Never Treated', 'Always Treated', 'Treated 5-6 Mo.'），但前两张交互状态图存在显示瑕疵。；图形暗示量纲混淆风险：三张图均使用同一纵轴（Resolutions Per Hour）和横轴（Agent Tenure, Months），未见不同量纲直接比较的明显错误；但第一、二张图中红色/蓝色曲线起点不一致（红约1.4，蓝从1.0起），而第三张原图显示三组在t=0时均≈1.0–1.2，存在视觉不一致，可能源于截图裁剪或渲染差异，无法确认是否为同一数据源。；操作后关系可辨性存疑：第一张图仅显示蓝/红线，无绿线；第二张图引入绿线但标注为'Treated'而非'Treated 5 mo.'，且与蓝线在第4个月交汇（横坐标≈4），而第三张原图明确绿线在第5个月（横坐标≈5）才偏离蓝线；时间点偏移（4 vs 5月）导致‘第5个月干预转折’这一关键因果推断在截图中难以可靠辨识。；文字描述与图示存在潜在冲突：实际状态文本称‘蓝色曲线从2.0次/小时起步’，但图中蓝线在t=0处明显低于2.0（≈1.0–1.2），与第三张原图一致；该矛盾表明文本描述可能误将‘目标值’或‘后期水平’当作起点，构成读图干扰。
- **cross-domain-first / macroeconomics-ai / baseline-tfp-estimate**：呈现包含不允许的属性：font-family
- **cross-domain-first / macroeconomics-ai / easy-vs-hard-tasks**：状态操作目标不存在：col-right
- **cross-domain-first / macroeconomics-ai / empirical-inequality**：呈现包含不允许的属性：visible
- **cross-domain-first / moral-machine / global_preferences**：呈现包含不允许的标签：hr
- **cross-domain-first / moral-machine / cultural_clusters**：状态控件与可达状态不一致
- **cross-domain-first / rag / rag-architecture**：图解视觉复核待处理：标签可读性：图中‘同一 z 用于所有 token’与‘不同 token 用不同 z_i’两行文字在截图中部分重叠、模糊，尤其在RAG-Token视图中，蓝色虚线箭头指向生成器的多个输入点，但文字标注位置紧邻且字号小，存在视觉干扰与辨识困难；虽DOM文本明确列出两者，但实际显示中未清晰区分其适用场景（即RAG-Sequence vs RAG-Token），导致操作后关系（如z是否共享）难以仅凭图像直接辨识。；图形暗示量纲混淆风险：检索器输出‘检索文档 z’标注为‘潜在变量 (Latent)’，而文档索引侧标注为‘稠密向量’；但图中从DPR到‘检索文档 z’再到BART的连线为实线单路径，未体现‘z’是向量集合还是具体文档片段；同时‘潜在变量’通常指低维连续表示，而‘稠密向量’是高维嵌入，二者在图中被并列呈现为同一节点内容，易误导读者认为可直接比较或等价替换，存在隐含量纲混用暗示。；操作后关系不可辨：在RAG-Token视图中，新增虚线箭头与‘不同 token 用不同 z_i’标注，但未明确标出z_i的来源（是否重新检索？是否从同一Top-K中采样？），也无时间/步骤序号标识生成器每步边缘化时z_i如何动态绑定；仅靠箭头与文字无法确认‘每一步都对Top-K文档进行边缘化’这一操作逻辑是否真实反映在图中结构上。
- **cross-domain-first / rag / qa-results**：qwen3-vl-plus 输出不完整：length
- **cross-domain-first / rag / retrieval-ablations**：qwen3-vl-plus 输出不完整：length
- **cross-domain-first / shannon / source-entropy-def**：呈现包含不允许的属性：visibility
- **cross-domain-first / shannon / noisy-channel-capacity**：模型结构校验失败：2 validation errors for Scene states.0.patches.0.attributes   Value error, 只允许SVG几何/颜色属性；可见性和高亮用外层visible/emphasize [type=value_error, input_value={'d': 'M 140 100 Q 270 60... 'fill-opacity': '0.15'}, input_type=dict]     For further information visit https://errors.pydantic.dev/2.12/v/value_error states.1.patches.0.attributes   Value error, 只允许SVG几何/颜色属性；可见性和高亮用外层visible/emphasize [type=value_error, input_value={'d': 'M 140 100 Q 270 20..., 'fill-opacity': '0.3'}, input_type=dict]     For further information visit https://errors.pydantic.dev/2.12/v/value_error
- **cross-domain-first / simulation-argument / prob-formalism**：图解视觉复核待处理：图中横轴标注为 'NI (平均模拟数)'，数值范围至 10^20；纵轴为 'f_sim'，无量纲（比例），二者量纲不同，但图中直接绘制在统一坐标系中，未说明是否已归一化或对数处理，可能误导读者认为可直接线性比较。虽常见于示意性曲线图，但严格来说属于‘明显暗示不同量纲直接比较’的视觉风险。；三难困境命题框在第二张图中被置于曲线上方并用红色箭头指向曲线高处，与第一、三张图中该框位置不同（第一张图中该框未出现，第三张图中该框位置与第一张类似但文字内容相同），存在布局不一致问题，影响‘操作后关系是否可辨’——即状态切换时关键注释的位置变化未清晰标示其对应逻辑节点。；公式中分母为 '(Pf · fI · NI) + 1'，但PDF原文（第三张）给出的推导式为 f_sim = (f_p * N_bar * H_bar) / ((f_p * N_bar * H_bar) + H_bar)，其中 H_bar 是非模拟观察者数量。截图中的简化公式隐去了 H_bar，且将 N_bar 替换为 NI，未明确说明 NI 是否等价于 N_bar * H_bar 或其他组合，导致从图到公式的映射关系模糊，影响‘操作后关系是否可辨’。；标签文字基本可读，无严重重叠；但‘三难困境命题’框在第二张图中覆盖部分曲线，轻微遮挡，属轻微可读性问题，未达‘严重重叠’程度，故不列为关键 issue。
- **cross-domain-first / simulation-argument / sim-cost-estimate**：图解视觉复核待处理：标签可读性问题：图中存在多处文字重叠或位置冲突。例如，'10^14-10^17 单脑/秒'、'10^33-10^36 全人类历史' 与横轴刻度及主标注 '10^42 ops/sec 行星质量计算机 (1 秒)' 在视觉上密集堆叠，未清晰区分层级；尤其在 state-brain-ops 和 state-capacity-compare 中，'单脑/秒' 和 '全人类历史' 标注紧贴横轴，易被误读为坐标轴标签而非数据点说明。；量纲混淆风险：图中所有数值均以 'ops/sec'（每秒操作数）为单位，但 '全人类历史总成本' 实际应为累计操作总数（ops），即 'ops = ops/sec × 时间'；而图中将其标为 '10^33–10^36' 并置于 ops/sec 纵轴上，暗示其为速率量，构成明显量纲错位。同理，'行星质量计算机 (1 秒)' 的 10^42 ops/sec 是瞬时算力上限，而人类历史模拟成本若为总操作数，则不能直接与之在相同对数坐标系中作水平比较——除非已归一化为等效持续速率（如平均速率），但图中未说明此转换。；操作后关系不可辨：图中绿色边框代表‘可用算力上限’，蓝色区域代表‘模拟需求’，但仅显示一个固定值（10^42 ops/sec）作为上限，而模拟需求在不同视图下分别为 10^14–10^17（单脑）、10^33–10^36（全人类历史总成本），三者物理意义不同（瞬时 vs 累计），且未标明时间尺度。因此，无法从图中明确判断‘运行一次模拟所需时间’或‘是否可在1秒内完成’等操作关系；例如，state-capacity-compare 中称‘仅需不到百万分之一的算力运行一秒即可完成’，但若全人类历史总成本为 10^36 ops，则需 10^36 / 10^42 = 10^{-6} 秒（即 1 微秒），逻辑上成立；然而该推导依赖外部假设（将总成本视为 ops，且算力为恒定 10^42 ops/sec），图本身未提供足够信息支撑此因果链，故操作后关系不可直接从图辨识。；数值标注歧义：'< 1/1,000,000' 出现在 state-capacity-compare 图中，位于 10^36 附近虚线处，但未说明是相对于什么的比值（是占 10^42 的比例？还是占某其他量？）。结合文本‘< 1/1,000,000’紧邻‘10^42 ops/sec’标注，易误认为是 10^42 的百万分之一（即 10^36），但若 10^36 是全人类历史总成本（ops），则其与 10^42 ops/sec 的比值无量纲意义，进一步加剧理解困难。
- **cross-domain-retest / adaptive-dcs-somp / adaptive-mechanism**：实际标签遮挡/裁切：[{"state_id": "state-init", "kind": "clipped_label", "target_ids": ["pm-label-1"], "ratio": 0.3654460061120295}, {"state_id": "state-focus", "kind": "clipped_label", "target_ids": ["pm-label-1"], "ratio": 0.3654460061120295}]
- **cross-domain-retest / attention / mt-results**：qwen3.5-plus 输出不完整：length
- **cross-domain-retest / cnnic55 / infra_resources_ipv6_5g**：实际标签遮挡/裁切：[{"state_id": "st_5g_cov", "kind": "label_overlap", "target_ids": ["pm-label-26", "pm-label-27"], "ratio": 0.6941829859366082}]
- **cross-domain-retest / generative-ai-work / experience_curve**：实际标签遮挡/裁切：[{"state_id": "state_baseline", "kind": "clipped_label", "target_ids": ["labelNever"], "ratio": 0.6160822471085001}, {"state_id": "state_baseline", "kind": "clipped_label", "target_ids": ["labelAlways"], "ratio": 0.6340468474087164}, {"state_id": "state_baseline", "kind": "clipped_label", "target_ids": ["thresholdText"], "ratio": 0.39507454808983256}]
- **cross-domain-retest / lyrics / style-structural-metrics**：实际标签遮挡/裁切：[{"state_id": "state-repeat", "kind": "clipped_label", "target_ids": ["label-rep-high"], "ratio": 0.37088247427941967}]
- **cross-domain-retest / lyrics / bias-validation-results**：实际标签遮挡/裁切：[{"state_id": "state-sign-consistency", "kind": "clipped_label", "target_ids": ["pm-label-2"], "ratio": 0.38}, {"state_id": "state-ft-superiority", "kind": "clipped_label", "target_ids": ["pm-label-2"], "ratio": 0.38}, {"state_id": "state-data-limitation", "kind": "clipped_label", "target_ids": ["pm-label-2"], "ratio": 0.38}]
- **cross-domain-retest / rag / qa-results**：qwen3-vl-plus 输出不完整：length
- **cross-domain-retest / simulation-argument / sim-cost-estimate**：交互检查未通过：["locator.waitFor: Timeout 15000ms exceeded.\nCall log:\n\u001b[2m  - waiting for locator('body[data-current-state]') to be visible\u001b[22m\n"]
- **release / attention / mt-results**：实际标签/可读性问题：[{"state_id": "state-enfr-discrepancy", "kind": "label_overlap", "target_ids": ["label-trans-enfr-body", "label-trans-enfr-table"], "ratio": 0.5384615384615384}, {"state_id": "state-cost-analysis", "kind": "label_overlap", "target_ids": ["label-cost-moe", "label-cost-ratio"], "ratio": 0.5833333333333334}]
- **release / generative-ai-work / experience_curve**：交互检查未通过：["locator.waitFor: Timeout 30000ms exceeded.\nCall log:\n\u001b[2m  - waiting for locator('iframe').contentFrame().locator('body[data-current-state]')\u001b[22m\n"]
- **release / lyrics / style-structural-metrics**：实际标签/可读性问题：[{"state_id": "state-repeat", "kind": "clipped_label", "target_ids": ["label-rep-high"], "ratio": 0.3889564263836188}]
- **release-candidate / adaptive-dcs-somp / simulation-results**：实际标签/可读性问题：[{"state_id": "state-initial", "kind": "contrast", "target_ids": ["val-time-non-ada"], "ratio": 1.18, "text": "84.63"}, {"state_id": "state-initial", "kind": "contrast", "target_ids": ["val-rmse-non-ada"], "ratio": 1.18, "text": "0.1334"}, {"state_id": "state-performance", "kind": "contrast", "target_ids": ["val-time-non-ada"], "ratio": 1.18, "text": "84.63"}, {"state_id": "state-performance", "kind": "contrast", "target_ids": ["val-rmse-non-ada"], "ratio": 1.18, "text": "0.1334"}]
- **release-candidate / attention / multi-head-attention**：1 validation error for LayoutReview issues.0.target_ids   List should have at most 3 items after validation, not 4 [type=too_long, input_value=['pm-label-1', 'pm-label-...-label-3', 'pm-label-4'], input_type=list]     For further information visit https://errors.pydantic.dev/2.12/v/too_long
- **release-candidate / attention / mt-results**：呈现包含不允许的属性：dy
- **release-candidate / generative-ai-work / main_productivity_result**：2 validation errors for LayoutReview issues.0.target_ids   List should have at most 3 items after validation, not 4 [type=too_long, input_value=['txt-increase-val', 'pm-...-label-5', 'pm-label-6'], input_type=list]     For further information visit https://errors.pydantic.dev/2.12/v/too_long issues.1.target_ids   List should have at most 3 items after validation, not 5 [type=too_long, input_value=['pm-label-3', 'pm-label-...abel-21', 'pm-label-22'], input_type=list]     For further information visit https://errors.pydantic.dev/2.12/v/too_long
- **release-candidate / generative-ai-work / heterogeneity_skill**：2 validation errors for LayoutReview issues.1.target_ids   List should have at most 3 items after validation, not 5 [type=too_long, input_value=['pm-label-4', 'pm-label-...-label-7', 'pm-label-8'], input_type=list]     For further information visit https://errors.pydantic.dev/2.12/v/too_long issues.2.target_ids   List should have at most 3 items after validation, not 4 [type=too_long, input_value=['pm-label-6', 'pm-label-...-label-8', 'pm-label-9'], input_type=list]     For further information visit https://errors.pydantic.dev/2.12/v/too_long
- **release-candidate / lyrics / style-structural-metrics**：1 validation error for VisualEvidence data.15.period   Field required [type=missing, input_value={'label': 'Target word se...onditions': 'Section 4'}, input_type=dict]     For further information visit https://errors.pydantic.dev/2.12/v/missing
- **release-candidate / lyrics / bias-validation-results**：实际标签/可读性问题：[{"state_id": "state-sign-consistency", "kind": "label_overlap", "target_ids": ["pm-label-27", "pm-label-29"], "ratio": 0.4740307242136064}, {"state_id": "state-ft-superiority", "kind": "label_overlap", "target_ids": ["pm-label-27", "pm-label-29"], "ratio": 0.4740307242136064}, {"state_id": "state-data-limitation", "kind": "clipped_label", "target_ids": ["status-text"], "ratio": 0.5}]
- **release-candidate / lyrics / bias-social-implication**：实际标签/可读性问题：[{"state_id": "state-impact", "kind": "label_overlap", "target_ids": ["pm-label-1", "pm-label-10"], "ratio": 0.5}, {"state_id": "state-comparison", "kind": "contrast", "target_ids": ["pm-label-4"], "ratio": 2.04, "text": "男/女名 vs 事业/家庭"}]
- **release-candidate / moral-machine / methodology_mm**：1 validation error for LayoutReview issues.1.target_ids   List should have at most 3 items after validation, not 12 [type=too_long, input_value=['pm-label-2', 'pm-label-...abel-22', 'pm-label-23'], input_type=list]     For further information visit https://errors.pydantic.dev/2.12/v/too_long
- **release-candidate / moral-machine / global_preferences**：1 validation error for LayoutReview issues.0.target_ids   List should have at most 3 items after validation, not 4 [type=too_long, input_value=['pm-label-9', 'pm-label-...abel-11', 'pm-label-12'], input_type=list]     For further information visit https://errors.pydantic.dev/2.12/v/too_long
- **release-candidate / simulation-argument / sim-cost-estimate**：实际标签/可读性问题：[{"state_id": "state-brain-rate", "kind": "clipped_label", "target_ids": ["pm-label-1"], "ratio": 0.567849780709149}, {"state_id": "state-history-total", "kind": "clipped_label", "target_ids": ["pm-label-1"], "ratio": 0.567849780709149}, {"state_id": "state-capacity-ratio", "kind": "clipped_label", "target_ids": ["pm-label-1"], "ratio": 0.567849780709149}, {"state_id": "state-brain-rate", "kind": "contrast", "target_ids": ["label-brain-val"], "ratio": 1, "text": "10^14-10^17"}, {"state_id": "state-history-total", "kind": "contrast", "target_ids": ["label-history-val"], "ratio": 1, "text": "10^33-10^36"}, {"state_id": "state-capacity-ratio", "kind": "contrast", "target_ids": ["label-history-val"], "ratio": 1, "text": "10^33-10^36"}]
- **release-verification / attention / mt-results**：实际标签/可读性问题：[{"state_id": "state-enfr-discrepancy", "kind": "label_overlap", "target_ids": ["label-trans-enfr-body", "label-trans-enfr-table"], "ratio": 0.5384615384615384}, {"state_id": "state-cost-analysis", "kind": "label_overlap", "target_ids": ["label-cost-moe", "label-cost-ratio"], "ratio": 0.5833333333333334}]
- **release-verification / generative-ai-work / experience_curve**：交互检查未通过：["locator.waitFor: Timeout 30000ms exceeded.\nCall log:\n\u001b[2m  - waiting for locator('iframe').contentFrame().locator('body[data-current-state]')\u001b[22m\n"]
- **release-verification / lyrics / style-structural-metrics**：实际标签/可读性问题：[{"state_id": "state-repeat", "kind": "clipped_label", "target_ids": ["label-rep-high"], "ratio": 0.3889564263836188}]
- **representative-first / attention / mt-results**：呈现包含不允许的属性：markerunits
- **representative-first / cnnic55 / infra_resources_ipv6_5g**：4 validation errors for SceneReview issues.0   Input should be a valid string [type=string_type, input_value={'type': 'data_misreprese...148对应2024年12月"]}, input_type=dict]     For further information visit https://errors.pydantic.dev/2.12/v/string_type issues.1   Input should be a valid string [type=string_type, input_value={'type': 'data_misreprese...引文中均未出现"]}, input_type=dict]     For further information visit https://errors.pydantic.dev/2.12/v/string_type issues.2   Input should be a valid string [type=string_type, input_value={'type': 'temporal_incons...间标注缺乏支撑']}, input_type=dict]     For further information visit https://errors.pydantic.dev/2.12/v/string_type issues.3   Input should be a valid string [type=string_type, input_value={'type': 'misleading_anno...几年，表述模糊"]}, input_type=dict]     For further information visit https://errors.pydantic.dev/2.12/v/string_type
- **representative-first / cnnic55 / commerce_payment_logistics**：呈现包含不允许的属性：xmlns
- **representative-first / simulation-argument / sim-cost-estimate**：状态属性越界：visible
- **representative-first / simulation-argument / bland-indifference**：呈现包含不允许的属性：stroke-linecap
- **representative-retest / attention / mt-results**：呈现包含不允许的属性：style
- **representative-retest / cnnic55 / exec_summary_key_metrics**：图解视觉复核待处理：{"type": "data_mismatch", "description": "图中显示2024年12月网民规模为11.08亿人（正确），但增长量标注为“+0.16亿”（即1600万人），而原文明确记载“较2023年12月增长1608万人”（见pdf-d20a33e7eb892f38-p7-b1, p23-b19, p23-b20）。0.16亿=1600万，与1608万存在8万人误差，虽小但属精确数据不一致。", "evidence": ["pdf-d20a33e7eb892f38-p7-b1: '较2023 年12 月增长1608'", "pdf-d20a33e7eb892f38-p23-b19: '较2023 年12 月增长1608 万人'", "pdf-d20a33e7eb892f38-p23-b20: '较2023 年12 月增长1608 万人'"]}；{"type": "data_mismatch", "description": "右侧图表中“互联网普及率”条形图显示2023年为77.5%、2024年为78.6%，但图中标注为“77.5%”和“78.6%”下方却写有“(4%)”，此“(4%)”无任何来源依据，且与原文“提升1.1个百分点”严重冲突。原文明确为+1.1pct（见p7-b2, p23-b20），而非4%。该“(4%)”疑似误将“78.6% - 77.5% = 1.1%”错误写作“4%”，或混淆了其他指标。", "evidence": ["pdf-d20a33e7eb892f38-p7-b2: '较2023 年12 月提升1.1 个百分点'", "pdf-d20a33e7eb892f38-p23-b20: '较2023 年12 月提升1.1 个百分点'", "图中条形图下方文字：'互联网普及率(4%)' —— 无依据且错误"]}；{"type": "misrepresentation", "description": "图解底部文字称“聚焦网民总规模，展示2023至2024年的绝对数量增长，强调突破11亿大关”，此表述虽方向正确，但结合图中“+0.16亿”与“11.08”并列呈现，易误导读者认为11.08亿是“突破11亿”的首次达成（实则2023年10.92亿已接近），而原文在第23页明确指出“我国网民规模已突破11亿人，达11.08亿人”，强调的是“已达”，非“首次突破”。更关键的是，图解将增长量简化为“+0.16亿”而省略精确值1608万, 属于信息降级且引入误差。", "evidence": ["pdf-d20a33e7eb892f38-p23-b16: '我国网民规模已突破11亿人，达11.08亿人'", "pdf-d20a33e7eb892f38-p23-b19: '截至2024年12月，我国网民规模突
- **representative-retest / cnnic55 / commerce_payment_logistics**：图解视觉复核待处理：{"type": "data_conflict", "description": "图解中‘网络支付用户规模’标注为‘10.29亿’，但未注明单位是‘万人’还是‘亿人’。根据原文（p39-b31, p39-b34），截至2024年12月，网络支付用户规模为‘10.29亿人’（即102,891万人），该数值本身正确；但图解下方文字说明‘展示网络支付的基础规模（10.29 亿）与无人机配送的累计基础数据（40 万单）’将‘10.29亿’与‘40万’并列，易被误解为‘10.29亿用户’ vs ‘40万订单’，而‘40万’单位是‘订单’而非‘用户’，二者量纲不一致，构成误导性对比。", "evidence": ["pdf-d20a33e7eb892f38-p39-b31: '截至2024 年12 月，我国网络支付用户规模达10.29 亿人'", "pdf-d20a33e7eb892f38-p39-b34: 用户规模数据为 '102891'（万人）"]}；{"type": "data_conflict", "description": "图解右侧‘即时配送创新场景’中标注‘累计订单≥40万’，但原文中无任何关于‘无人机外卖航线’或‘累计订单40万’的数据支撑。原文提及‘网上外卖用户规模达5.92亿人’（p39-b39），但未提供无人机配送的具体订单量。该‘40万’数据属无来源虚构，且与报告整体宏观统计口径不符（报告以亿级用户规模为主，极少出现‘万’级订单细节）。", "evidence": ["pdf-d20a33e7eb892f38-p39-b39: '截至2024 年12 月，我国网上外卖用户规模达5.92 亿人'", "全文未检索到‘无人机外卖’、‘40万订单’等关键词"]}；{"type": "misrepresentation", "description": "图解将‘政策驱动：以旧换新行动方案 & 通用航空装备创新应用’作为图表下方说明，但原文（p33）仅在总体描述中提及‘推动实数融合不断走深向实’及‘新业态、新场景不断涌现’，并未将‘以旧换新’与‘通用航空装备’明确列为驱动网络支付/即时配送增长的直接政策因素。该归因属于过度引申，混淆了宏观背景与具体因果关系。", "evidence": ["pdf-d20a33e7eb892f38-p33-b74~b76: 原文强调‘数字技术推动数字经济’、‘助力实体经济与数字经济深度融合’，未点名具体政策名称", "pdf-d20a33e7eb892f38-p33-b77~b79: 仅列出应用增长数据，未归因于特定政策"]}；{"type": "layout_issue", "description": "前两张图解中，按钮区域（如‘初始视图’等）存在视觉重叠/遮挡风险：第二张图中深蓝色按钮条覆
- **cross-domain-first / attention / 宿主**：没有通过核验的呈现，宿主保留原讲解
- **cross-domain-first / rag / 宿主**：没有通过核验的呈现，宿主保留原讲解
- **cross-domain-first / lyrics / 宿主**：没有通过核验的呈现，宿主保留原讲解
- **cross-domain-first / generative-ai-work / 宿主**：没有通过核验的呈现，宿主保留原讲解
- **cross-domain-first / macroeconomics-ai / 宿主**：没有通过核验的呈现，宿主保留原讲解
- **cross-domain-first / cnnic55 / 宿主**：没有通过核验的呈现，宿主保留原讲解
- **release-candidate / lyrics / 宿主**：没有通过核验的呈现，宿主保留原讲解
- **release-verification / attention / 宿主**：来源入口未显示对应原句：scene-caa5e699544c8d1383ac
- **release-verification / attention / 宿主**：来源入口未显示对应原句：scene-333b6a3d769e72e8c155
- **release-verification / rag / 宿主**：来源入口未显示对应原句：scene-52a7469f50b9f9d359fb
- **release-verification / rag / 宿主**：来源入口未显示对应原句：scene-2b50c5384109fffaaf5b
- **release-verification / rag / 宿主**：来源入口未显示对应原句：scene-a6ab1bdecc45db83d3f3
- **release-verification / adaptive-dcs-somp / 宿主**：来源入口未显示对应原句：scene-476a0fd37d6f0024b83b
- **release-verification / adaptive-dcs-somp / 宿主**：来源入口未显示对应原句：scene-2ffa5f89c893c244c49f
- **release-verification / adaptive-dcs-somp / 宿主**：来源入口未显示对应原句：scene-265b926d3d35b08f49cd
- **release-verification / shannon / 宿主**：来源入口未显示对应原句：scene-fcd6154a4797aafb84e6
- **release-verification / shannon / 宿主**：来源入口未显示对应原句：scene-e0e8b3bf9315ccc0a691
- **release-verification / shannon / 宿主**：来源入口未显示对应原句：scene-fbca1904647a280684a2
- **release-verification / lyrics / 宿主**：来源入口未显示对应原句：scene-01228f078b48548ac91c
- **release-verification / lyrics / 宿主**：来源入口未显示对应原句：scene-602abd507a6cae93e60c
- **release-verification / moral-machine / 宿主**：来源入口未显示对应原句：scene-73c302a57e110000f2e2
- **release-verification / moral-machine / 宿主**：来源入口未显示对应原句：scene-ec00166c186d732b4eb0
- **release-verification / moral-machine / 宿主**：来源入口未显示对应原句：scene-a137f99c13ae0a4f22cf
- **release-verification / simulation-argument / 宿主**：来源入口未显示对应原句：scene-15dafa4887b8b9e42957
- **release-verification / simulation-argument / 宿主**：来源入口未显示对应原句：scene-d811d17a94e8e4152244
- **release-verification / simulation-argument / 宿主**：来源入口未显示对应原句：scene-ca8f055fbbfea137c12c
- **release-verification / generative-ai-work / 宿主**：来源入口未显示对应原句：scene-7ee81246edbafe01968d
- **release-verification / cnnic55 / 宿主**：来源入口未显示对应原句：scene-ccce59c489719caaedba
- **representative-first / attention / 宿主**：图内来源未能回查：scene-907a959d25daaf5629ea
- **representative-first / attention / 宿主**：图内来源未能回查：scene-03e37dea5a767159abc5
- **representative-first / simulation-argument / 宿主**：图内来源未能回查：scene-73e2591378832aee4f3b
- **representative-retest / cnnic55 / 宿主**：locator.click: Timeout 30000ms exceeded. Call log: [2m  - waiting for locator('[data-state="state-total"]').first()[22m [2m    - locator resolved to <button type="button" class="btn-primary" aria-pressed="true" data-state="state-total">总规模突破</button>[22m [2m  - attempting click action[22m [2m    - waiting for element to be visible, enabled and stable[22m [2m    - element is visible, enabled and stable[22m [2m    - scrolling into view if needed[22m [2m    - done scrolling[22m [2m    - <strong>第 55 次中国互联网络发展状况统计报告核心论证覆盖图 · 第 1 页</strong> from <aside aria-label="阅读伴侣" class="rightbar is-open">…</aside> subtree intercepts pointer events[22m [2m  - retrying click action[22m [2m    - waiting for element to be visible, enabled and stable[22m [2m    - element is visible, enabled and stable[22m [2m    - scrolling into view if needed[22m [2m    - done scrolling[22m [2m    - <aside aria-label="阅读伴侣" class="rightbar is-open">…</aside> intercepts pointer events[22m [2m  - retrying click action[22m [2m    - waiting 20ms[22m [2m    - waiting for element to be visible, enabled and stable[22m [2m    - element is visible, enabled and stable[22m [2m    - scrolling into view if needed[22m [2m    - done scrolling[22m [2m    - <article class="source-entry">…</article> from <aside aria-label="阅读伴侣" class="rightbar is-open">…</aside> subtree intercepts pointer 
- **cross-domain-retest / attention / mt-results / 可见操作**：No renderable candidate: inspect generation/structure failure
- **cross-domain-retest / rag / qa-results / 可见操作**：No renderable candidate: inspect generation/structure failure
- **release-candidate / attention / mt-results / 可见操作**：No renderable candidate: inspect generation/structure failure
- **release-candidate / lyrics / style-structural-metrics / 可见操作**：No renderable candidate: inspect generation/structure failure

## 能力边界与解释

模型为具体节点生成专属HTML/SVG/CSS和有限状态快照；没有执行模型生成的JavaScript，也没有建立学科组件库。首版覆盖有限枚举状态，不包含任意连续仿真或模型训练复现。原正文仍保持完整。

交互检查比较SVG几何/路径/高亮或数据行的实际变化，文字说明变化本身不算通过。浏览器验证包含所有离散状态、重置、网络请求和窄屏；视觉模型抽看首末状态，来源核验读取全部状态，不能据此声称所有视觉细节均经过人工检查。

只发布全部检查通过且正文哈希匹配的呈现。被阻断的场景保留原图文；文档ready仍是既有正文质量状态，不能当作图解全部成功的依据。发布阶段和最终回归结果另见本报告后续状态。

## 默认发布记录

```json
{
  "published_at": "2026-10-25T05:14:37+08:00",
  "scope": "Local default release of validated scenes; blocked scenes retain original text",
  "cases": [
    {
      "case_id": "attention",
      "document_id": "pdf-bdfaa68d8984f0dc",
      "job_id": "ba30bacb-06ce-4fab-8b9a-7055d405c097",
      "published": 2,
      "blocked": 1
    },
    {
      "case_id": "rag",
      "document_id": "pdf-23e3249e9a1e7541",
      "job_id": "5272d5ae-845f-4ea0-83fa-2f756bc96a04",
      "published": 3,
      "blocked": 0
    },
    {
      "case_id": "adaptive-dcs-somp",
      "document_id": "pdf-b4deafe808239771",
      "job_id": "d6ddcc1c-5382-4aa9-bc96-bc194b8da573",
      "published": 3,
      "blocked": 0
    },
    {
      "case_id": "shannon",
      "document_id": "pdf-6e4e3411984f3edf",
      "job_id": "786b3bf2-48f5-40e5-9ad9-4873ed138553",
      "published": 3,
      "blocked": 0
    },
    {
      "case_id": "lyrics",
      "document_id": "pdf-66fe209b72eb93c6",
      "job_id": "530ddf47-b87b-4308-b2e9-e635b4244624",
      "published": 2,
      "blocked": 1
    },
    {
      "case_id": "moral-machine",
      "document_id": "pdf-59c4f6158add045b",
      "job_id": "7ddf6bbd-dcac-4972-adbe-bd23b87c3f75",
      "published": 3,
      "blocked": 0
    },
    {
      "case_id": "simulation-argument",
      "document_id": "pdf-be823e12764a35cd",
      "job_id": "8fc52bc7-adb6-4e29-823b-03eade2f2b47",
      "published": 3,
      "blocked": 0
    },
    {
      "case_id": "generative-ai-work",
      "document_id": "pdf-ac0a4e183aa6f936",
      "job_id": "faeb82ce-8cf5-4b6e-b1b3-625899e7fc1c",
      "published": 2,
      "blocked": 1
    },
    {
      "case_id": "macroeconomics-ai",
      "document_id": "pdf-b0183405d850db11",
      "job_id": "8784ffa1-b672-422e-b5f3-c414d5e12865",
      "published": 3,
      "blocked": 0
    },
    {
      "case_id": "cnnic55",
      "document_id": "pdf-d20a33e7eb892f38",
      "job_id": "c836855d-3682-4720-a71f-7c46fbe5c16f",
      "published": 3,
      "blocked": 0
    }
  ],
  "published_scenes": 27,
  "blocked_scenes": 3,
  "protected_user_tables_unchanged_before_release": true,
  "backup": "artifacts/presentation-release/prepublish.db",
  "remaining_repairs": "Attention mt-results label overlap; lyrics style-structural-metrics label clipping; generative-ai-work experience_curve initialization timeout",
  "default_enabled": true,
  "tests": {
    "backend_total": 44,
    "fixture_browser_groups": 7,
    "real_qwen_browser": "passed on isolated database/PDF copy",
    "source_diagnostic": "Exact textContent match; prior host source mismatch caused by innerText whitespace collapse",
    "default_browser_representatives": [
      "attention",
      "simulation-argument",
      "cnnic55"
    ],
    "default_browser_status": "passed",
    "default_browser_scene_count": 8,
    "visible_audit_passed": 30,
    "visible_audit_states": 93
  },
  "protected_user_tables_unchanged_after_release": true,
  "verified_at": "2026-10-25T05:17:14+08:00",
  "auto_pending_repair": false
}
```
