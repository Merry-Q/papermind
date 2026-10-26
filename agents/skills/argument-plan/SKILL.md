---
name: argument-plan
version: 0.2.0
description: 根据全文和账本生成核心论证覆盖图。
---

输入：全文章节树与 ClaimLedger，不只读取向量检索返回的几个片段。

任务：识别问题、主张、方法机制、关键推理、证据与局限之间的关系，按照文档自身论证组织阅读顺序。白皮书、研报不强制套算法论文模板。

输出 ArgumentPlan：required_nodes、optional_nodes、dependencies、claim_ids、coverage_map、unresolved_gaps。每个节点注明必须解释的目标和来源。正式 Schema 待 D2 落地。

核心公式、变量、条件进入必需节点；详细推导可作可选展开。不要按固定读者等级重写，不增加理解测试。概念关系不自动等于必要先修关系。

退出条件：全文核心论证都有承载节点或明确缺口。任何核心缺口都不能通过缩小覆盖范围悄悄消失。
