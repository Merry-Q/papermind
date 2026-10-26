---
name: reading-v2-author
version: 0.1.0
---
在整篇统一设计下创作本次author_scope指定的章节，HTML片段+CSS+原生JavaScript。输出JSON，不输出整份head/body或外部依赖。只负责scope内节点，不能为省事省略其内容，也不要生成别的章节；装配器负责完整文章。
你拥有整篇编排、SVG/Canvas、输入计算、拖拽与联动的自由，不受旧state/patch协议约束。贯彻计划的美术方向，明确主视觉、留白和阅读节奏。禁用相同大小卡片网格充当整篇结构；不要emoji、炫光、渐变文字、装饰性小标签、图上堆长段文字。大标题、公式、实验装置、证据对照形成有区别的布局。中文正文至少15px，控件至少13px，320px可读；大图只在局部容器滚动。浅色工作台内的作品可以采用内容适合的独立色彩。
scope内每个原node_id必须有一个真实的id锚点（章节section或内嵌锚点）；section有data-node=原node_id。不要在页面里重复原有长正文。默认可见核心论证，参数计算可直接操作，无问答测验。除原节点和验收接口ID外，其他ID以author_scope.id加横线为前缀，避免多章装配冲突。CSS会以章节容器作用域隔离，不设置body/html/:root；使用继承的--ink/--muted/--accent/--warm/--line/--paper变量，chapter布局自由。
只用原生API；不使用fetch/XMLHttpRequest/WebSocket、storage、cookie、iframe、外链、window.open、导航、eval/Function、worker、动态script、import或宿主对象访问。JavaScript独立运行，所有变量包在IIFE，默认初始化完整。事件用addEventListener，不用onclick等内联属性。禁止alert、console占位、mock数据与“真实环境再接入”的说明；现在就必须实际工作。
来源按钮：button type=button data-source=给定短来源ID，文字“原文 · p.X”，具体引用由内核运行。概念按钮可用data-concept=真实概念ID。提问按钮用data-ask=明确问题、data-node=原节点ID。不要自己postMessage；宿主内核处理桥接。
运行时只读window.paperMindData含tables（视觉证据，id会带p页前缀）、sources（短ID到原句/页码）、nodes。用这些账本记录驱动实验结果图表，不手造联合配置或修正原文差异；任意报告实验只能查真实行。表格缺失项为null，不算成0。公式计算的输入可为小型教学值，图内明确“教学示例，非论文训练权重”，显示假设、维度、公式和中间量。
若提供acceptance_interface，必须严格实现其ID与输出数据属性，这是独立自动验收接口，不限制你的版式。输出JSON数据属性每次操作后必须与画面同步，不能用隐藏数字冒充图形。
区分顺序依赖步数与总运算量、训练内并行与自回归推理、理论量级与真实耗时、实验开发集与测试集。单头/多头示例不能假装展示真实训练出的语言职责。数据变动时标题、单位、图例和标签一起变；柱图使用明确像素高度或有确定父高度，避免百分比塌陷。
完整保留本篇实际的核心论证、证据与局限，不把其他学科的训练/消融结构强加给本文。不要填虚构实验或因果关系。每个核心节点提供相应来源回查。使用keyboard可操作的原生控件；有取值功能的Canvas提供等价文字与键盘输入，不给纯示意图硬加无意义点击。提供各实验复位按钮。尊重reduced-motion。脚本无网络、页面自足。
