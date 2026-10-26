# Attention V2 问题与分批处理

范围：仅 Attention。三篇代表材料、原十篇回归未启动。

## 生成准备与首稿

- 计划使用已存在的 canonical 来源 ID，短 ID 契约未兼容。通过精确映射归一化，保留原计划，不重调模型。
- 计划未选消融与泛化的表页。根据全文真实表格依赖补齐原页，记录 visual-dependencies.json。
- 首次整篇编写遗漏 scaled-dot-product/multi-head-attention/training-regime/generalization-parsing 锚点，Q/K/V、位置维度、结果与消融操作接口未按要求实现；部分来源未正确对应；原稿被拦截，未发布。
- 首稿自行复制少量实验数据并写了 mock/alert 占位行为，违背只读账本要求。
- Page 8 视觉抽取重复使用 BLEU 和 Training Cost 列名，多级表头被字典覆盖，EN-DE 丢失。
- Page 9 视觉抽取将 A 组的 h 错位到 d_ff，B 组的 d_k 错位到 h，C 组部分 d_model/d_ff 错位到 N。原 PDF 图像和原生文本共同揭示差错。
- 浏览器检查首次在缺失截图目标处提前结束。调整检查器跳过该截图并继续其余操作，使用同一份冻结首稿补跑整批；此项属于测试器修正，不是产品修复。

原始首稿、数据和独立 HTML：data/reading-v2/079275a4-bac5-4953-b1ff-e449a44ef573/first-draft。
首稿检查：artifacts/reading-v2/first-draft-complete/report.json。

以上内容在首稿测试期间只作记录，待整批结束后集中修订。

## 分章节首批与集中修订

该批先完成15组页面检查、8组宿主检查和模型事实/体验评审，再修改产物。

实质问题：PE奇数维频率使用了dim/d而非2·floor(dim/2)/d；Canvas点击没有换算显示缩放；部分可见输出没有按行为契约绑定；BLEU只展示少数模型；手机横向溢出；PDF返回时iframe尚未展开导致滚动位置被提前钳制。以上均已定向修复，原批次保留于chapter-first-frozen。

另外补充了多头的真实投影/拼接计算、注意力中间量、首屏结构比较、实验口径边界与零权重真实零高度。移除了没有足够同口径依据的精确成本降幅和“300K steps=更多数据”的暗示。

模型评审的误报经过Codex对原页/代码/轨迹/截图回查，未盲从：

- 要求解释41.0/41.8差异原因：原文未交代，不能编造归因；页面保留差异并明确原因未说明。
- 要求补充GPU实测吞吐和解码延迟：原文未报告，且当前呈现明确是理论量级，不应为满足评审编造实验。
- 称自注意力顺序操作应为O(n)：与原Table1的O(1)相矛盾，保留正确内容。
- 称PE没有颜色和坐标说明：最终页面在热力图紧邻上方明确给出颜色、轴含义和范围；点击和键盘输入经过公式核验。
- 称权重输出未区分：已有显式Σ(权重×V)中间量，最后再补权重范围/位置/零基线/无单位及加权输出不是概率的说明。

不把视觉模型的pass/revise当作最终事实，也不隐去其原始意见。工程复核结论见experience-disposition.json；不声称已经测得真实学习增益。

## 最终验证

- 页面16组全部通过：artifacts/reading-v2/final-verification/report.json。
- 宿主8组全部通过，PDF返回位置3079→3079，无业务写请求：artifacts/reading-v2/final-host/report.json。
- 独立网页5项通过：artifacts/reading-v2/standalone.json。
- 来源模型复核pass，覆盖十个核心节点：artifacts/reading-v2/verification/fidelity-review.json。
- 后端54项通过；TypeScript与生产构建通过。构建仍有原有包体积提示。

最终变更后只做本篇相关验证，未启动其他材料测试或切换其他文档默认呈现。

## 最终原句回查补正

打开用户交付页逐条回查时，发现模型事实复核曾漏掉的三项：标签平滑的困惑度变化写反；架构脚本动态引用使用canonical ID且短ID替换遇到b1/b11前缀冲突；成本段落残留旧语言口径。撤回该预览的validated状态，集中纠正后再验。

四步架构逐步点击并回查完成，来源依次为[S074,S036]、[S037,S070]、[S068]、[S071,S074]；最后的FFN按钮实际打开了对应的原句。加入动态来源越界拦截及回归测试。标签平滑与成本静态段落已与原句/表注保持一致。详见artifacts/reading-v2/final-source-check.json。未重生未受影响的图形和公式。
