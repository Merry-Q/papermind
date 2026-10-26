# 关键数据与事务契约

> 2026-10-25 实现状态更新：已接入阿里千问生成、OCR、视觉提问、真实联网和来源对照核验。本文下方保留初期方案/测试历史，不作为当前能力声明。当前运行说明见根 README，实测与未解决问题见 docs/LIVE-BOUNDARY-REPORT.md、docs/FIRST-PASS-ISSUES.md；运行契约以 backend/live_contracts.py 为准。


状态：正式开发建议。Demo 的实际 HTTP 契约以 backend/contracts.py 和 /docs 为准。规范化存储草案见 schema-v1.sql，不能直接作为 Demo 数据库迁移执行。

## Claim 与引用

```json
{
  "id":"claim-coverage",
  "statement":"缩小候选区域的前提是仍覆盖真实目标",
  "kind":"paper",
  "critical":true,
  "conditions":["候选裁剪阶段","不代表后续恢复必然正确"],
  "source_ids":["source-method-p2"],
  "verification":"pending"
}
```

这是结构例子，不指向一篇真实论文。Claim 的 kind 表示解释的性质，Source 的 kind 表示证据来源。教学推演可以引用论文公式，但推演产生的新数值仍属于 teaching。

SourceAnchor 的完整服务端形态：

```json
{
  "id":"source-method-p2",
  "document_version_id":"version-id",
  "file_hash":"sha256-of-file",
  "parser_version":"parser-config-hash",
  "kind":"paper",
  "physical_page":2,
  "printed_page":"1",
  "block_id":"p2-b4",
  "bbox":[0.12,0.25,0.88,0.43],
  "rotation":0,
  "quote":"实际抽取的原句",
  "quote_hash":"sha256-of-original-quote",
  "locator_status":"unresolved"
}
```

坐标必须满足 0≤x0<x1≤1、0≤y0<y1≤1。页码、坐标、引文都以文件版本为范围；不靠标题和页码拼接唯一键。

## KnowledgeCard

```json
{
  "id":"card-id",
  "question":"这个公式中的 A 在表示什么？",
  "concept_key":"observation-matrix",
  "domain":"sparse-recovery",
  "definition_version":"v1",
  "layer":"intuition",
  "body":"具有证据支持的本层解释",
  "paper_connection":"A 的列与当前候选位置的对应关系",
  "conditions":["当前观测模型"],
  "source_ids":["source-formula"],
  "next_links":[{"concept_key":"linear-map","relation":"optional_background"}],
  "return_anchor":{"lesson_id":"lesson-id","node_id":"formula","block_id":"formula-1"}
}
```

next_links 的关系可为 explanation_dependency 或 optional_background。模型生成的前置关系保留证据与待核对状态，不能直接写成经验证课程图谱。

## 页面 Patch

正式版操作只允许 insert_block、replace_block、hide_block。原始生成版本保持不可变，个人页面通过 overlay 渲染；重生成时做三方合并（旧基础、新基础、个人 overlay），冲突进入预览。

```json
{
  "id":"patch-id",
  "lesson_id":"lesson-id",
  "base_revision":7,
  "message_id":"assistant-message-id",
  "operations":[{"type":"insert_block","target_node_id":"mechanism","after_block_id":"mechanism-body","block":{"id":"user-supplement-id","kind":"paragraph","text":"待确认补充"}}],
  "source_ids":["source-method"],
  "status":"preview"
}
```

提交事务：BEGIN IMMEDIATE → 比较当前 revision → 检查允许节点和来源 → 检查幂等键 → 写 overlay 与 Patch 状态 → revision 加一 → COMMIT。任一失败回滚，返回 409 或 422。模型不能通过工具绕过用户确认。

撤回不是把 revision 减一，而是提交一个逆向 overlay 并增加 revision。Demo 仅实现追加补充和按最近顺序撤回，不实现任意块替换或三方合并。

## 对话与工具回执

每条用户消息保存 reading_anchor、selection、attachment_snapshot；助手消息保存实际 source_ids、action_id、模型配置和运行状态。

```json
{
  "action_id":"action-id",
  "type":"set_search_scope",
  "document_id":"document-id",
  "node_id":"mechanism",
  "component_id":"candidate-grid",
  "arguments":{"scope":"narrow"},
  "expected_component_revision":3
}
```

前端回执包括 action_id、status、old_state、new_state、component_revision、error。动作失败时模型应解释失败，不宣称画面已改变。未知动作或过期组件直接拒绝。

## 事件与重连

SSE 每条事件以持久 event_id 为 ID，不使用前端生成的临时序号。

```json
{
  "event_id":42,
  "type":"node_readable",
  "run_id":"run-id",
  "document_version":"version-id",
  "node_id":"mechanism",
  "revision":8,
  "checks":{"fact":"pass","structure":"pass","browser":"pass"}
}
```

此示例表示该节点在所定义范围内通过三个检查，不代表全篇 ready。整篇完成必须另有 run_completed，且检查必需节点覆盖与核心缺口。

## 概念库与偏好

- ConceptLibrary：用户主动保存，包含 explanation_id、layer、conditions、self_reported 和保存时间。它不自动由聊天生成。
- PreferenceMemory：对话形成、可撤回，包含明确偏好描述、source_message_id 和删除抑制记录。不得推导全局能力等级。
- 用户删除某项偏好后，同一稳定 key 不自动重建；未来若主动重启，才解除抑制。
- 特殊定义或条件变更时，即使知识层级命中，仍要解释差异。

Demo 按三种固定概念复用，不具备通用概念消歧、条件匹配与定义版本迁移能力。
