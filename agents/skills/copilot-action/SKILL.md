---
name: copilot-action
version: 0.2.0
description: 将明确的用户操作请求转换为演示动作或页面修改提案。
---

输入：用户请求、当前位置、组件状态、参数边界、页面 revision。

仅当用户明确要求操作演示时产生白名单 action；工具只允许修改当前文档已存在的演示。执行前校验组件存在与参数合法，保存旧状态并等待执行回执。未收到成功回执，回答不得宣称已完成。

页面修改输出 PatchProposal，包含 base_revision、target_node、changes、source_ids、message_id。模型不能直接提交正文变更；由用户预览、确认后调用应用 API。

禁止直接写概念库、删除原文件、执行代码、扩大文献检索范围。附加文献必须来自用户明确选择。

未知操作返回说明及可用操作，不拼接 JavaScript。版本冲突要求刷新预览，不覆盖已有用户修改。
