# 整篇交互讲解：生成即展示

2026-10-26 更新。本文是当前实现；旧版 V1 节点图解已移除。

## 唯一产品链路

上传 PDF → 解析/OCR → 组织正文与引用 → 整篇交互规划 → 图表数据提取 → 并行生成章节代码 → 装配 → 自动发布 → 前端呈现。

1. `backend/main.py` 上传文件，`backend/jobs.py::run_job` 提取内容并生成规范正文和概念，保留 Copilot、引用、补充、个人概念库使用的稳定节点。正文生成过程不再调用事实 reviewer、coverage 或质量修订循环。
2. `run_job` 直接创建整篇版本，调用 `reading_v2.generate`；原任务直到交互页面发布才显示完成。正文完成后交互生成失败，可单独重试整篇页面，不必重做正文。
3. `reading_v2.evidence` 汇集原文、节点、概念与来源短 ID。planner 加载 reading-v2-plan，给出整篇论点、3–9 个章节、视觉方向、交互动作与边界。
4. vision 读取必要原页的表格、列名、值和条件，存入 `data.json`。作者通过只读的 `window.paperMindData.tables` 获取原文数据。
5. `reading_v2_author.compose` 最多并行编写三个章节，加载 reading-v2-author，输出 HTML/CSS/JavaScript。输入变化在浏览器中重算并更新 SVG/Canvas，无需每次请求模型。
6. 后端标准化引用和锚点、隔离章节 ID/CSS/常用 DOM 操作，加入主标题、导航和边界，形成完整 `artifact.json` 与 HTML。
7. 生成成功直接在同一数据库事务中写入 completed 状态和 reading_defaults 默认指针，无验收审批、手动发布或浏览器检查。前端轮询原生成任务和 reading_job，完成后自动打开新页面。

## 产品与测试的职责

产品只处理输出格式、可执行资源边界、任务状态、取消、失败恢复及文档归属。CSP 和 opaque-origin iframe 沙箱继续限制外部网络与宿主访问。章节缺少锚点、来源质量、公式正确性、图形是否真正变化和视觉体验均由测试检查，不设为产品发布门槛。

`backend/tests/reading_checks.py` 提供离线结构/引用检查；后端回归测试与通用浏览器测试工具负责验收。生产生成不加载该模块，也不启动浏览器。

Copilot、知识递归补充、个人库、原 PDF、补充预览和撤回保持原业务流程；不属于本次删除范围。

## 状态与接口

- `POST /api/documents/{did}/reading-v2`：单独生成/重试整篇页面；同一文档的重复请求复用正在运行的任务。
- `GET /api/documents/{did}`：原正文任务及 reading_job 状态。
- `POST /api/documents/{did}/reading-v2/{eid}/cancel`：请求取消。
- `GET /api/documents/{did}/reading-v2/default`：当前默认版本。
- `GET /api/documents/{did}/reading-v2/{eid}/artifact?channel=...`：可运行的完整页面。
- `GET /api/documents/{did}/reading-v2/{eid}/export`：独立 HTML。

生命周期为 queued → running → completed，异常为 failed/cancelled。生成失败保留上次可用默认页；运行器代码更新不会因“未重新验收”隐藏已有页面。

服务启动将产物齐全且对应当前正文的旧 draft/validated 版本迁移为 completed 并更新默认页，不重新调用模型；失败/缺失产物不被当作生成成功。数据库中的旧节点图解记录仅作为历史数据留存，产品没有对应执行链路或 API。

## 核心代码

- backend/jobs.py：PDF 到整篇交互的任务衔接、进度、取消与恢复。
- backend/reading_v2.py：证据、规划、视觉数据、生成、自动发布与持久状态。
- backend/reading_v2_author.py：并行章节创作与装配。
- backend/reading_v2_routes.py：生成、呈现、取消和导出接口。
- backend/model_gateway.py：阿里模型调用、skill 加载、格式重试和用量审计。
- frontend/src/App.tsx、ReadingV2.tsx：进度轮询、自动切换与沙箱阅读。

默认 planner/composer 为 qwen3.5-plus，vision 为 qwen3-vl-plus，OCR 为 qwen3.5-ocr。实际模型可由后端配置覆盖。
