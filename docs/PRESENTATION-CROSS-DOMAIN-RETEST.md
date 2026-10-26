# 十篇跨领域呈现复测：完成记录

记录时间：2026-10-25T03:39:27+08:00。当前范围是测完和记录，未进行本批问题修复、效率优化或默认发布。

## 结果

- 原10篇全部完成生成测试，30幅候选：22幅通过当前管线，8幅阻断。每篇至少有1幅本批管线通过的候选。
- 十篇受保护的文档字段哈希全部不变，包括规范节点、来源、概念、文档内补充、对话和patch。该哈希不代表对独立概念库表另做了全表快照。
- 宿主十篇全部通过：本批22幅、70个状态，操作有图形变化、来源回查可用，1440/1024/736/390/320阅读区无横向溢出，未检出前端运行异常。
- 追加可见操作审计：28幅可渲染候选、88个状态通过；另外2幅缺少可渲染产物。只改变隐藏元素或解说不算通过；每个状态均比较可见几何、计算样式和数据标签。
- 人工抽查在一幅管线通过的CNNIC图中发现2项漏检。因此22是技术管线通过数，不能当作22幅最终发布合格数。
- 默认呈现未开启，发布产物数为0，本批没有遗留排队/运行任务。

## 逐篇结果

| 材料 | 管线通过 | 管线阻断 | 宿主检查 | 受保护字段不变 |
|---|---:|---:|---|---|
| adaptive-dcs-somp | 2 | 1 | passed | True |
| attention | 2 | 1 | passed | True |
| cnnic55 | 2 | 1 | passed | True |
| generative-ai-work | 2 | 1 | passed | True |
| lyrics | 1 | 2 | passed | True |
| macroeconomics-ai | 3 | 0 | passed | True |
| moral-machine | 3 | 0 | passed | True |
| rag | 2 | 1 | passed | True |
| shannon | 3 | 0 | passed | True |
| simulation-argument | 2 | 1 | passed | True |

## 八幅管线阻断

- **adaptive-dcs-somp / adaptive-mechanism**：实际标签遮挡/裁切：[{"state_id": "state-init", "kind": "clipped_label", "target_ids": ["pm-label-1"], "ratio": 0.3654460061120295}, {"state_id": "state-focus", "kind": "clipped_label", "target_ids": ["pm-label-1"], "ratio": 0.3654460061120295}]
- **attention / mt-results**：qwen3.5-plus 输出不完整：length
- **cnnic55 / infra_resources_ipv6_5g**：实际标签遮挡/裁切：[{"state_id": "st_5g_cov", "kind": "label_overlap", "target_ids": ["pm-label-26", "pm-label-27"], "ratio": 0.6941829859366082}]
- **generative-ai-work / experience_curve**：实际标签遮挡/裁切：[{"state_id": "state_baseline", "kind": "clipped_label", "target_ids": ["labelNever"], "ratio": 0.6160822471085001}, {"state_id": "state_baseline", "kind": "clipped_label", "target_ids": ["labelAlways"], "ratio": 0.6340468474087164}, {"state_id": "state_baseline", "kind": "clipped_label", "target_ids": ["thresholdText"], "ratio": 0.39507454808983256}]
- **lyrics / style-structural-metrics**：实际标签遮挡/裁切：[{"state_id": "state-repeat", "kind": "clipped_label", "target_ids": ["label-rep-high"], "ratio": 0.37088247427941967}]
- **lyrics / bias-validation-results**：实际标签遮挡/裁切：[{"state_id": "state-sign-consistency", "kind": "clipped_label", "target_ids": ["pm-label-2"], "ratio": 0.38}, {"state_id": "state-ft-superiority", "kind": "clipped_label", "target_ids": ["pm-label-2"], "ratio": 0.38}, {"state_id": "state-data-limitation", "kind": "clipped_label", "target_ids": ["pm-label-2"], "ratio": 0.38}]
- **rag / qa-results**：qwen3-vl-plus 输出不完整：length
- **simulation-argument / sim-cost-estimate**：交互检查未通过：["locator.waitFor: Timeout 15000ms exceeded.\nCall log:\n\u001b[2m  - waiting for locator('body[data-current-state]') to be visible\u001b[22m\n"]

分类：4幅标签裁切、1幅标签重叠、1次编写输出截断、1次视觉输出截断、1次浏览器初始化超时。初始化超时的哲学图在追加独立审计中能操作，但根因尚未定位；保留原阻断，不改成成功。

## 人工补充问题

CNNIC commerce_payment_logistics：

1. 高亮样式将白字改成蓝字，落在深蓝背景上；12px文字实测对比度2.04:1。视觉门槛主要阻拦可测的遮挡/裁切，未有效阻止该低对比度问题。
2. 原p42-b22“历史累计完成订单超40万单”，图和初始说明写“40万单”，丢失下界限定。来源模型判supported未发现该精度问题。裸数值绑定仍不足以保留完整事实限定。

以上两项已保留计算样式、原句、截图和节点证据，尚未修复。操作有效不能证明语义和显示完全正确。

## 版本、中断与耗时

冻结清单中的后端呈现代码、运行器、skill和浏览器校验脚本哈希全部一致。本批仅新增只读的追加测试脚本及报告，不更改产品运行代码。
上次对话中断后后台进程停止，已保存中断快照并恢复原4个job_id。已结束的6篇未重跑；恢复任务复用阶段缓存，部分浏览器检查重执行。四篇耗时包含中断，不作正常生成速度基准。
监控期间有一次本机HTTP连接中断，服务与生成任务仍在运行；监控改读持久状态后完成，问题单独保存。
最终模型审计共105条记录，包含复用与失败尝试，elapsed含部分并发排队和重试；不是105次必需成功调用或干净冷启动成本。具体角色/token分布见性能快照。

## 原始证据

- 本批生成、宿主、可见操作、人工抽查与最终校验：data/presentation-benchmarks/cross-domain-retest/。
- 原首轮：data/presentation-benchmarks/cross-domain-first/，没有覆盖。
- 图稿、来源包、原始模型输出、逐状态浏览器报告：data/presentation-runs/{job_id}/{node_id}/。
- 宿主桌面/手机截图：artifacts/presentations/cross-domain-retest/。
- 中断前快照：同目录interruption-1/；性能快照：artifacts/presentation-performance/baseline-final.json。
- 完整历史汇总：PRESENTATION-IMPLEMENTATION-REPORT.md；问题账本：PRESENTATION-BATCH-ISSUES.md。

## 待后续集中处理

布局边界与标签碰撞；模型输出长度及失败阶段重试；初始化稳定性；受信高亮的文字对比度；数字连同“超/约/截至/同比”等限定的保真与复核。效率方案仍为GENERATION-EFFICIENCY-PLAN.md中的计划，没有在本批中实施。
