# paperMind

阿里云完整版入口：https://papermind.47.237.109.221.sslip.io/ ，打开即可使用。部署结构与备份操作见 [阿里云部署说明](deploy/README.md)。

专业 PDF 本地阅读工作台：阿里千问生成整篇交互讲解，支持来源回查、图表/区域提问、递归知识补充、Copilot、个人概念库及可撤回的页面补充。React + TypeScript + Vite / FastAPI / SQLite。

当前交互页面的实际后端实现见[交互生成链路](docs/INTERACTIVE-GENERATION-BACKEND.md)；测试资产清理范围、保留摘要与待执行清单见[清理记录](docs/maintenance/2026-10-26/README.md)。

当前是本机单用户版本。产品不预置教学文档；导入真实 PDF 后使用配置的模型生成。教学 fixtures 仅用于隔离测试。

## 在线交互阅读

GitHub Pages 地址：https://merry-q.github.io/papermind/ 。在线版提供数据库中默认已发布版本的交互讲解、公式、引用回查和原 PDF，不需要 API 密钥。新生成、OCR、联网与 Copilot 请运行下面的本地完整版；GitHub Pages 不运行 Python 后端。

推送 main 后，`.github/workflows/pages.yml` 自动从已提交数据构建和发布，不调用模型。导出仅包含默认已发布页面及对应 PDF，不包含数据库、聊天记录、个人概念库或服务端配置。可用 `python scripts/build_pages.py` 在本地生成 `.pages/site`，并用静态 HTTP 服务预览该目录。

## 启动

需要 Python 3.11+、Node.js 22.12+、阿里云百炼密钥和模型权限。在项目根目录 PowerShell 执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
npm install
npm --prefix frontend ci
Copy-Item .env.example .env.local
```

编辑 `.env.local` 填写 `DASHSCOPE_API_KEY`。同名系统环境变量优先；密钥仅由后端读取。当前环境已配置可用密钥，无需重填。修改配置后重启服务。

```powershell
npm run dev
```

打开 http://127.0.0.1:5173。也可构建后只启动一个服务：

```powershell
npm run build
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

打开 http://127.0.0.1:8000，API 文档在 http://127.0.0.1:8000/docs。无密钥时可阅读已保存的真实文档；新生成、OCR、联网不可用。

## 模型分工

| 任务 | 阿里模型 | 配置名 |
|---|---|---|
| 全文计划 | qwen3.5-plus | PAPERMIND_MODEL_PLANNER |
| 连续讲解 | qwen3.5-plus | PAPERMIND_MODEL_COMPOSER |
| Copilot 回答核验 | qwen-plus | PAPERMIND_MODEL_REVIEWER |
| 对话/递归知识 | qwen-plus | PAPERMIND_MODEL_COPILOT |
| 原页视觉/图表核验 | qwen3-vl-plus | PAPERMIND_MODEL_VISION |
| 扫描 OCR | qwen3.5-ocr | PAPERMIND_MODEL_OCR |
| 联网检索 | qwen-plus | PAPERMIND_MODEL_SEARCH |

全部发往阿里云 DashScope。Chat Completions 兼容协议不代表使用其他模型供应商。默认中国内地端点，区域和模型权限需匹配。输出使用 JSON Object + 服务端 Pydantic/业务校验，不声称供应商端严格 Schema 保证。

## 使用

1. 导入 PDF 后自动排队生成，段落逐步出现；完成后自动展示整篇交互页面。
2. 沿主线阅读机制、结果、条件及局限。步骤演示按内容选择，不强加模拟数据滑块。
3. 点击引用回查原句，或切换原 PDF、选页/框选提问，再返回讲解位置。
4. 在右栏查阅概念、继续深入一层，或让 Copilot 沿具体问题取证；没有理解测验或掌握评分。
5. 概念按层级由用户自选保存。页面补充另行预览、确认应用，并可撤回；两个动作独立。
6. 每篇文档一条连续对话，保留阅读锚点。明确问题直接回答；深度问题先给出可调整的研究计划，确认后显示取证与核验进度。任务可以停止并在刷新后恢复。显式附加另一篇文献后，可对照提问并分别查来源。

上传后的唯一生成链路为：PDF 解析/OCR → 正文与来源组织 → 整篇交互规划 → 图表数据提取 → 并行章节代码生成 → 页面装配 → 自动发布到前端。章节由千问编写 HTML/CSS/JavaScript，在沙箱 iframe 中呈现；引用、概念和问题继续连接原工作台。

生成成功即更新默认阅读页，不需要事实、计算、体验、浏览器验收或手动发布。质量检查只在开发测试中运行。产品保留数据格式约束、沙箱及资源访问限制、任务取消、失败重试与历史页面回退。已移除节点图解队列、API、运行器和前端入口。

已生成的历史草稿在服务启动时迁移为可展示版本，不重新调用模型。缺失产物或生成失败的版本不作为已完成页面。界面显示生成进度，并在完成后自动打开整篇交互讲解。

## 边界

- 20 MB / 120 页上限，不支持加密文件。默认每篇 OCR 30 页、视觉预读 2 页，可通过环境变量调整。2 页预读不代表所有图表已核验；其他页可主动提问。
- 全文文字进入计划，过长时逐页归纳。双栏排序是启发式，OCR/视觉可能读错，保留原页。
- 实际联网搜索并读取学术/机构网页或 PDF 正文，过滤首页和明显不相关内容；仍可能无可读可靠来源。外部 PDF 最多读取前 12 页，来源显示读取范围。
- ready 表示正文生成完成；交互页面任务另有 queued/running/completed/failed/cancelled 状态。有引用不等于支持；不足的回答显示提示并禁止加入页面。
- 跨文档概念复用目前基于领域/标题/层级键，尚无完整语义等价和适用条件推理。
- 长文可能生成数分钟并产生 API 费用。支持取消、保留阶段产物、重试及用量审计；文档用量累计包含早期迭代，不能当最终账单。
- 当前无应用内账号、多人隔离或计费系统。阿里云部署公开访问，所有访问者可查看和操作同一份文档、阅读记录与概念库。

详见 [边界报告](docs/LIVE-BOUNDARY-REPORT.md)、[首轮问题账本](docs/FIRST-PASS-ISSUES.md)、[10 篇语料与固定版本](docs/CORPUS-SOURCES.md)。首轮测试与集中修复复测分开保存。

## 验证

```powershell
python -m unittest discover -s backend/tests -v
npm run check
npm run build
npm run test:e2e
node scripts/e2e-live.mjs
```

离线测试/教学 E2E 使用隔离数据；真实 E2E 需要运行中的服务并调用模型。浏览器默认使用已安装的 Microsoft Edge。

```powershell
python scripts/prepare_corpus.py
python -u scripts/benchmark_live.py --extended --workers 3
```

真实基准通过前端相同 API 上传、生成、问答和事务检查。`--regenerate` 重新调用模型；`--output data/benchmark-after-fixes` 单独保存复测。派生单页扫描另用 `--include-derived --ids attention-page3-scan`，不算第11篇独立论文。

## 工程与数据

| 位置 | 职责 |
|---|---|
| frontend/ | 阅读、公式/Markdown、页图、受控交互、知识与对话 |
| backend/jobs.py | 持久队列、阶段产物、正文组织、整篇交互生成衔接 |
| backend/reading_v2.py | 整篇交互生成、持久状态、自动发布与历史迁移 |
| frontend/reading-v2-runtime.js | 整篇交互页面的事实账本与宿主桥接 |
| backend/model_gateway.py | 千问调用、并发/重试、结构校验、用量记录 |
| backend/parser.py | PDF IR、原句锚点、OCR、视觉预读 |
| backend/retrieval.py | 文档检索、联网、学术索引及正文取证 |
| backend/live_copilot.py | 锚定问答、深度研究计划、取证、回答核验与受控动作 |
| backend/copilot_runs.py | 持久对话任务、计划确认、阶段事件、取消与恢复 |
| agents/skills/ | 按阶段加载的应用任务规范，见 agents/README.md |
| tests/corpus/ | 文献来源、版本、hash、页数与边界清单 |
| docs/ | 产品决策、原开发方案、实测及已知问题 |
| data/ | SQLite、上传文件、解析缓存、任务及测试原始产物 |

默认数据在项目 data/，可用 PAPERMIND_DATA_DIR 更改。PDF 文本、所选页图/区域及提问会发送给配置的阿里模型，联网发送检索词。当前仓库按所有者要求提交 data/ 中的 PDF、数据库与生成结果；`.env.local`、artifacts/、数据库 WAL/SHM 与依赖仍忽略。部署所需密钥请仅配置在本地后端环境中。

[原开发方案](docs/DEVELOPMENT-PLAN.md) 保留历史规划。运行时契约以 backend/contracts.py 和 backend/live_contracts.py 为准。
