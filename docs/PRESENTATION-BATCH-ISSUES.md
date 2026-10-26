# 呈现升级批次问题账本

2026-10-25。先完成批次再集中修复，首轮记录不覆盖。

## 三篇代表材料首轮

9幅候选图解：4通过、5阻断。三篇规范正文和用户内容哈希不变。

1. 合法SVG的stroke-linecap、markerUnits与xmlns声明被过严拒绝。修复仅扩展无网络/脚本的合法几何属性；固定SVG命名空间声明移除，不允许其他URL。
2. 可见性写入attributes而非patch.visible。只对明确true/false作无损规范化，冲突仍报错；其他未知状态属性继续拒绝。
3. 视觉审查issues返回结构化对象，原校验期望字符串。保留完整对象文本和insufficient裁决，不把格式兼容当作内容通过。
4. 3幅图将状态和来源绑在同一按钮，原运行器只执行状态。来源现在由可信运行器提供独立入口，不改变主应用来源逻辑。
5. 高亮描边继承到SVG文字，造成数字难读。只给几何形状描边，文字采用字重与填色。
6. 小屏SVG被整体缩小，字体可能过小。改为图内受控横向探索，父阅读区保持无溢出。
7. 人工补充发现：CNNIC首幅混合量纲比较、两个时点被画成趋势，尽管模型判supported，仍要求修复；反馈记录在manual-review.json，并强制同节点重新生成。
8. 修复后沿用原plan和node_id；已通过产物重新运行浏览器、视觉与事实检查，失败节点原稿及反馈一并提供，不换题绕过。

本轮不会把“按钮能点”或模型单一通过标签当作交互正确性的证据。

## 三篇同计划复测

9幅：6通过、3阻断。Attention/哲学宿主来源已通过；CNNIC宿主脚本因上一材料保留390px并打开侧栏，下一场景被侧栏遮挡而超时，属于测试前置状态未恢复，保留失败并修正脚本。

- 支持经同样CSS资源检查的行内布局样式，仍拒绝URL、代码和外部依赖。
- 精度仍需改进：1608万人不应被模型手写成0.16亿而不注明近似。新增原文字面量value_tokens，可由HTML data-value和状态text_token绑定显示，避免重写数值。
- 原呈现策划本身要求无依据的跨年曲线；新增原文对照的策划修正阶段，保留节点范围，收窄操作到实际证据。
- 视觉模型收到截断上下文，错称原文无“40万单”；原p42-b22确有该数据。视觉阶段改为显示/可读性检查，提供准确DOM文字；完整事实检查仍读取实际全部取证上下文，不用截图未见证明全文不存在。
- 三篇代表材料的失败节点继续沿用；十篇固定版本批次会同时验证修复与其余七篇的泛化。首轮与复测不覆盖。

## 十篇跨领域首轮（全部结束后集中修复）

27幅候选：4通过、23阻断；歌词材料计划输出缺字段，整项失败。十篇宿主检查已完成，四篇有本批可用图解，其余保留原讲解。不是成功发布状态。

- 9项为DOM/属性/学术排版协议问题（sub、font-family、visibility等），另有目标引用、步骤映射、状态可达性与模型输出长度问题。
- 10项由视觉模型阻断，其中包含真实标签/轴问题，也有明显误判：将不同X/Y轴的不同单位认为不可绘图、要求图写全正文维度、用两个约数相减否定原文1608万人等。
- 修复采用具体LayoutIssue类别与DOM标签定位，几何测量支持遮挡/裁切判定；语义/事实继续由完整原文阶段独立核验，不由视觉模型擅自扩展。
- 对真实单位、轴、曲线与图例问题逐节点提供反馈，保留原节点范围；不能把它们归入误报后直接接受旧稿。
- 为不合法DOM引用增加一次有记录的结构纠错，保留首次原稿与结构错误；不是删除失败证据。协议兼容只扩展安全排版/几何，不执行模型代码。
- 目标修复及复测记录在cross-domain-retest新目录，不覆盖本轮。

## 十篇跨领域复测（全部结束，暂不修复）

本批30幅候选，管线22通过、8阻断；十篇正文、来源、对话、页面补充等受保护文档字段哈希全部不变。代码、skill及运行器与批次implementation.json逐项一致。首轮和复测分目录，不覆盖历史失败。

| 问题 | 材料与节点 | 记录 |
|---|---|---|
| 标签裁切 | 通信 adaptive-mechanism | 两状态同一标签超出图形范围 |
| 标签裁切 | 生成式AI与工作 experience_curve | 基线状态的三处标签部分超出图形范围 |
| 标签裁切 | 人文 style-structural-metrics / bias-validation-results | 共两幅，涉及状态标签与横轴说明 |
| 标签重叠 | CNNIC infra_resources_ipv6_5g | 5G状态标签重叠比例约0.694，几何与视觉共同确认 |
| 编写输出截断 | Attention mt-results | qwen3.5-plus返回length；没有可渲染产物 |
| 视觉输出截断 | RAG qa-results | qwen3-vl-plus返回length；没有可渲染产物 |
| 初始化超时 | 哲学 sim-cost-estimate | 管线等待body状态15秒超时；追加独立审计可正常操作，原因未定位，不抹除原失败 |

宿主页面十篇全部通过：仅计本批job_id的22幅、70个状态，来源入口可回查；1440/1024/736/390/320阅读区未检出横向溢出，未检出前端运行错误。预览中可能存在历史已验证候选，已从本批通过数中排除。

追加可见操作审计检查全部可渲染候选，包括被布局等检查阻断的图稿：28幅、88状态通过，每个控件有不同的可见图形或数据结果；两幅因输出失败不可渲染。该审计过滤隐藏元素并比较实际计算样式，不把仅隐藏DOM属性改变作为成功。操作有效仍不能替代布局与来源忠实性。

### 人工抽查发现的审查漏检

CNNIC commerce_payment_logistics虽被管线判validated，仍有以下两项问题，不能直接发布：

1. state_policy中受信高亮样式将原白字改为#315cc8，而底色为#26364b，实测12px文字对比度仅2.04:1。现有视觉门槛对tiny_text/contrast主要保留建议，没有完整的确定性检查，导致漏拦。
2. 原p42-b22为“历史累计完成订单超40万单”，图中文字和初始状态说明写成“40万单”，丢失下界限定。来源模型仍判supported，说明不能把模型支持标签等同精度完全正确。

人工证据、计算样式与来源对照保存在本批manual-review.json；后续修复须一并保留“超”等限定词，不能只绑定裸数字。

### 运行与计时问题

上次对话中断后服务及测试进程停止。已保留interruption-1快照，在冻结代码下恢复原4个任务ID，未新建任务或重跑已结束六篇。原有阶段缓存保留，恢复过程仍重新执行部分浏览器检查。另一次监控HTTP连接中断未影响服务，改为读取持久状态后完成记录。

含中断的四篇耗时已标duration_includes_interruption，不能用于正常冷启动承诺。完整调用统计另存artifacts/presentation-performance/baseline-final.json，包含恢复/失败尝试，累计调用时间不等于用户墙钟。

本批结束时尚未修复上述问题、尚未实施效率优化、尚未默认发布。下一轮应分别验证布局、输出预算/失败阶段恢复、初始化稳定性、对比度门槛和限定词保真。详细汇总见PRESENTATION-CROSS-DOMAIN-RETEST.md。

## 发布候选首批（全部生成结束，等待宿主检查）

10篇30候选：19通过、11阻断，正文及用户受保护字段均未变。原CNNIC限定词和重叠图修复通过；RAG、香农、宏观经济全通过。剩余失败保留如下：

- attention / multi-head-attention：1 validation error for LayoutReview issues.0.target_ids   List should have at most 3 items after validation, not 4 [type=too_long, input_value=['pm-label-1', 'pm-label-...-label-3', 'pm-label-4'], input_type=list]     For further information visit https://errors.pydantic.dev/2.12/v/too_long
- attention / mt-results：呈现包含不允许的属性：dy
- adaptive-dcs-somp / simulation-results：实际标签/可读性问题：[{"state_id": "state-initial", "kind": "contrast", "target_ids": ["val-time-non-ada"], "ratio": 1.18, "text": "84.63"}, {"state_id": "state-initial", "kind": "contrast", "target_ids": ["val-rmse-non-ada"], "ratio": 1.18, "text": "0.1334"}, {"state_id": "state-performance", "kind": "contrast", "target_ids": ["val-time-non-ada"], "ratio": 1.18, "text": "84.63"}, {"state_id": "state-performance", "kind": "contrast", "target_ids": ["val-rmse-non-ada"], "ratio": 1.18, "text": "0.1334"}]
- lyrics / style-structural-metrics：1 validation error for VisualEvidence data.15.period   Field required [type=missing, input_value={'label': 'Target word se...onditions': 'Section 4'}, input_type=dict]     For further information visit https://errors.pydantic.dev/2.12/v/missing
- lyrics / bias-validation-results：实际标签/可读性问题：[{"state_id": "state-sign-consistency", "kind": "label_overlap", "target_ids": ["pm-label-27", "pm-label-29"], "ratio": 0.4740307242136064}, {"state_id": "state-ft-superiority", "kind": "label_overlap", "target_ids": ["pm-label-27", "pm-label-29"], "ratio": 0.4740307242136064}, {"state_id": "state-data-limitation", "kind": "clipped_label", "target_ids": ["status-text"], "ratio": 0.5}]
- lyrics / bias-social-implication：实际标签/可读性问题：[{"state_id": "state-impact", "kind": "label_overlap", "target_ids": ["pm-label-1", "pm-label-10"], "ratio": 0.5}, {"state_id": "state-comparison", "kind": "contrast", "target_ids": ["pm-label-4"], "ratio": 2.04, "text": "男/女名 vs 事业/家庭"}]
- moral-machine / methodology_mm：1 validation error for LayoutReview issues.1.target_ids   List should have at most 3 items after validation, not 12 [type=too_long, input_value=['pm-label-2', 'pm-label-...abel-22', 'pm-label-23'], input_type=list]     For further information visit https://errors.pydantic.dev/2.12/v/too_long
- moral-machine / global_preferences：1 validation error for LayoutReview issues.0.target_ids   List should have at most 3 items after validation, not 4 [type=too_long, input_value=['pm-label-9', 'pm-label-...abel-11', 'pm-label-12'], input_type=list]     For further information visit https://errors.pydantic.dev/2.12/v/too_long
- simulation-argument / sim-cost-estimate：实际标签/可读性问题：[{"state_id": "state-brain-rate", "kind": "clipped_label", "target_ids": ["pm-label-1"], "ratio": 0.567849780709149}, {"state_id": "state-history-total", "kind": "clipped_label", "target_ids": ["pm-label-1"], "ratio": 0.567849780709149}, {"state_id": "state-capacity-ratio", "kind": "clipped_label", "target_ids": ["pm-label-1"], "ratio": 0.567849780709149}, {"state_id": "state-brain-rate", "kind": "contrast", "target_ids": ["label-brain-val"], "ratio": 1, "text": "10^14-10^17"}, {"state_id": "state-history-total", "kind": "contrast", "target_ids": ["label-history-val"], "ratio": 1, "text": "10^33-10^36"}, {"state_id": "state-capacity-ratio", "kind": "contrast", "target_ids": ["label-history-val"], "ratio": 1, "text": "10^33-10^36"}]
- generative-ai-work / main_productivity_result：2 validation errors for LayoutReview issues.0.target_ids   List should have at most 3 items after validation, not 4 [type=too_long, input_value=['txt-increase-val', 'pm-...-label-5', 'pm-label-6'], input_type=list]     For further information visit https://errors.pydantic.dev/2.12/v/too_long issues.1.target_ids   List should have at most 3 items after validation, not 5 [type=too_long, input_value=['pm-label-3', 'pm-label-...abel-21', 'pm-label-22'], input_type=list]     For further information visit https://errors.pydantic.dev/2.12/v/too_long
- generative-ai-work / heterogeneity_skill：2 validation errors for LayoutReview issues.1.target_ids   List should have at most 3 items after validation, not 5 [type=too_long, input_value=['pm-label-4', 'pm-label-...-label-7', 'pm-label-8'], input_type=list]     For further information visit https://errors.pydantic.dev/2.12/v/too_long issues.2.target_ids   List should have at most 3 items after validation, not 4 [type=too_long, input_value=['pm-label-6', 'pm-label-...-label-8', 'pm-label-9'], input_type=list]     For further information visit https://errors.pydantic.dev/2.12/v/too_long

发布候选宿主检查全部结束：9篇有本批通过图，歌词材料无通过图而正确保留正文；可见操作审计28幅可渲染候选全部操作有效，2幅不可渲染。冻结哈希无变化。集中修复：放宽同一显示问题的标签ID列表上限（仍保留具体问题），增加合法tspan dx/dy兼容，缺失统计时间明确记未标注；独立视觉结构纠错一次。11个失败节点有可审计人工稿，原稿保留，所有稿继续完整来源和显示核验。

## 本地默认发布

按用户“先更新发布”的最新指示，发布release-verification的27幅通过场景，默认开启。未发布3幅：Attention mt-results标签重叠、歌词style-structural-metrics标签越界、工作研报experience_curve初始化超时。文字修订稿已准备但尚未进入下一轮完整验收，不作为已修复发布。

原CNNIC“超40万单”限定丢失及深底蓝字问题已修复并重新通过，所有显示状态无硬性对比度问题。哲学速率/总量改为分区关系展示并经来源复核。审查ID列表过短、合法dx/dy不兼容等协议问题已修复。

release-verification宿主新增原句精确比对时使用innerText直接比较原文换行，引起系统性误报；另有侧栏异步更新等待不足风险。独立诊断证明原句textContent与源quote逐字一致，现测试等待规范化原句匹配后判断。旧失败记录不覆盖。默认入口attention/cnnic55/simulation-argument三篇已用修正后脚本通过，数据见release/host-default-browser.json。

发布后44项后端测试通过；原7组教学浏览器流程通过；真实千问回归在隔离数据库和PDF副本通过。十篇默认API返回27幅published，3幅未发布。正式documents/messages/patches/library/memories表发布前后hash完全一致。发布备份与记录见artifacts/presentation-release/prepublish.db及data/presentation-benchmarks/release.json。无下一轮自动生成或后台修复任务遗留。

## 发布验收批次
10篇30候选：27通过、3阻断；正文及用户字段哈希均不变。剩余：Attention mt-results两个标签重叠；歌词style-structural-metrics未计入父组平移导致标注越界；工作研报experience_curve在30秒内未完成iframe初始化。原图稿和原失败保留，定向修订记录在remaining-corrections.json。
