# paperMind 模型任务

应用通过 model_gateway 加载本地 skill 提示词，并调用阿里千问；不启动外部 Codex 进程。

| 任务 | 实际职责 |
|---|---|
| evidence-ledger / argument-plan | 提取原文、页码、来源与全文论证结构 |
| interactive-lesson | 生成规范正文、公式和概念，为整篇页面和 Copilot 提供共享节点 |
| reading-v2-plan | 规划整篇阅读主线、章节、美术方向和有意义的交互 |
| reading-v2-author | 并行编写各章 HTML/CSS/JavaScript，由后端装配发布 |
| knowledge-expansion | 按用户问题补充前置知识，连接个人概念库 |
| copilot-action | 原工作台的受控动作约定 |
| fact-review | 测试时可选的事实检查规范，不参与页面生成发布门槛 |

产品生成成功即发布；没有验收审批阶段，不自动启动浏览器或质量评审模型。模型输出仍需可解析的 JSON 和字段格式，执行代码仍受沙箱与资源限制。Copilot 对话及知识补充的既有逻辑保持不变。
