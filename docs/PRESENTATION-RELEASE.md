# paperMind 本地呈现发布记录

发布：2026-10-25T05:14:37+08:00；核对：2026-10-25T05:17:14+08:00。

已开启本地默认呈现，地址 http://127.0.0.1:8000/ 。原10篇共发布27幅独立图解；3幅仍保留原讲解。用户最新指示为先更新发布，本次不再等待或自动启动剩余修复。

## 发布内容

呈现独立于规范正文、Copilot、知识递归和概念库。模型生成文档专属HTML/SVG/CSS与有限状态，受信运行器执行，不运行模型生成JS。新文档正文核验完成后自动排队生成图解；图解失败不会把已核验正文改为incomplete。

界面显示图解进度、取消、单独重试和失败原因。已发布图解默认嵌入原节点，失败场景仍可读原图文。发布按正文、所用来源及渲染版本绑定，过期图解停止显示。

本轮修复了多处标签裁切/重叠、深色背景高亮文字对比度、数值超/约等限定词丢失、合法SVG属性兼容、视觉输出结构纠错，以及失败后不必整篇重写的问题。CNNIC原文“超40万单”现保留“超”；政策背景高亮文字保留白字。

## 逐篇发布数

| 材料 | 发布图解 | 未发布 |
|---|---:|---:|
| attention | 2 | 1 |
| rag | 3 | 0 |
| adaptive-dcs-somp | 3 | 0 |
| shannon | 3 | 0 |
| lyrics | 2 | 1 |
| moral-machine | 3 | 0 |
| simulation-argument | 3 | 0 |
| generative-ai-work | 2 | 1 |
| macroeconomics-ai | 3 | 0 |
| cnnic55 | 3 | 0 |

## 仍未发布的3幅

- Attention / mt-results：结果比较图仍有两组标签重叠。
- 歌词材料 / style-structural-metrics：父组平移后标注仍超出SVG边界。
- 生成式AI与工作 / experience_curve：本轮30秒初始化超时，尚未定位稳定根因。

前两幅已有定向文字坐标修订稿，尚未走下一轮完整验收；第三幅保留失败证据。它们没有通过发布门槛，不计入27幅。不能将本地默认发布解释为所有问题都已修完。

## 验证

- 后端44项通过；前端类型检查及构建通过。构建仍有原有单包体积提示。
- 原7组教学浏览器流程通过：对话、概念库、递归、来源/PDF返回、页面补充事务与跨文献等。
- 真实千问浏览器回归在隔离数据副本通过：真实概念保存/移出、原句回查、PDF框选、next_step动作和执行回执、小屏阅读。首次副本PDF路径设置错误已单独记录，修正测试数据后重跑通过。
- 十篇默认接口均enabled=true，只返回published，共27幅；无需presentationPreview参数。
- 普通入口Attention、CNNIC和哲学三篇实际操作、来源精确回查及1440/1024/736/390/320宽度检查通过。
- release-verification追加审计：30幅可渲染图、93个状态有不同的可见图形或数据结果；操作有效不代替显示/语义通过。
- 正式documents/messages/patches/library/memories表发布前后逐表hash一致，未修改原正文、对话、页面补充或概念库。

来源测试曾把innerText折叠的空白与含换行的原文直接比较而误报，独立诊断证明textContent逐字一致。改用等待规范化原句匹配；原测试失败记录保留，默认入口复测通过。

## 发布与回退

本次仅更新当前本机服务，没有云部署或公开外网发布。服务仍绑定127.0.0.1。发布前SQLite备份：artifacts/presentation-release/prepublish.db。
如需关闭默认图解，在服务端环境设置PAPERMIND_PRESENTATIONS_DEFAULT=0并重启；这会关闭默认展示和新正文完成后的自动图解队列，不删除正文、对话、概念库及已保存产物。

## 证据与边界

- 发布清单：data/presentation-benchmarks/release.json；十篇普通接口：release/default-api.json；三篇默认宿主：release/host-default-browser.json。
- 所有历史批次和失败保留在presentation-benchmarks；修订稿及原稿hash在presentation-runs对应job/node的review-correction.json。
- 最终测试、隔离真实对话记录、备份和来源诊断：artifacts/presentation-release/。
- 模型核验不是人工同行评审，有限状态图解不代表实验复现或已证明学习效果。长PDF效率方案尚未全面实施，上传仍为20MB/120页，不宣称已实现30%提速。
