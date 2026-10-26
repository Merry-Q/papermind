"""Authored teaching fixtures; these are not claims from a published paper."""
from copy import deepcopy

CONCEPTS = {
    "candidate": {"id": "candidate", "title": "候选空间", "layer": "definition", "lead": "先确定去哪里找，再决定如何找。", "text": "候选空间是当前允许算法考虑的所有可能位置。在这个教学例子里，每一个网格都是一个可能的位置。缩小范围会减少候选数，但真实目标必须仍在范围内。", "why": "它连接了计算量和漏检风险：少看一些位置更省计算，也可能把正确位置排除在外。", "next": "sparse", "source_ids": ["demo-method"]},
    "sparse": {"id": "sparse", "title": "稀疏表示", "layer": "intuition", "lead": "很多可能性，只有少数真正发生。", "text": "把所有候选位置的强度写成一个向量 x。绝大多数分量是零，少数非零分量表示目标的位置和强度，这就是此处的稀疏表示。稀疏不等于信号弱，而是非零分量少。", "why": "这说明为什么可以从较少的观测中寻找少数目标；能否唯一、稳定地恢复，还取决于观测矩阵、噪声与稀疏程度。", "next": "matrix", "source_ids": ["demo-formula"]},
    "matrix": {"id": "matrix", "title": "观测矩阵", "layer": "intuition", "lead": "把位置假设，连接到可以测到的信号。", "text": "在 y = Ax + ε 中，A 的每一列表示一个候选位置对观测的影响，x 是位置强度，y 是实际观测。只保留候选位置，相当于取 A 的部分列；若真实位置对应的列被删去，模型就无法准确表达原来的目标。", "why": "主线中的缩小搜索，不只是少画几个网格，也是在改变算法允许解释观测的模型集合。", "next": None, "source_ids": ["demo-formula"]},
}

SOURCES = [
    {"id": "demo-problem", "kind": "paper", "title": "教学文档 · 问题定义", "page": 1, "quote": "在一个含有 48 个候选位置的合成网格中，我们考察限定候选范围对搜索成本和目标覆盖的影响。候选位置的枚举次数仅作成本代理，不代表实际算法耗时。", "locator": "问题定义，第 1 段", "status": "fixture", "url": None},
    {"id": "demo-method", "kind": "paper", "title": "教学文档 · 方法与条件", "page": 2, "quote": "先从粗定位给出的区域中选取候选位置，再进行局部搜索。只有当该区域仍包含真实目标时，缩小候选集合才不会在这一步直接排除真实解。", "locator": "方法，第 2 段", "status": "fixture", "url": None},
    {"id": "demo-formula", "kind": "paper", "title": "教学文档 · 观测模型", "page": 3, "quote": "采用教学模型 y = Ax + ε。y 表示观测，A 表示观测矩阵，x 表示候选位置上的目标强度，ε 表示噪声。缩小候选空间等价于限定允许非零的坐标。", "locator": "式 (1) 与符号说明", "status": "fixture", "url": None},
    {"id": "demo-evidence", "kind": "teaching", "title": "教学数据 · 网格枚举", "page": 4, "quote": "网格共 8 列、6 行。全域枚举 48 个候选位置，局部区域枚举 16 个，极窄区域枚举 4 个。目标固定在第 6 列、第 3 行，极窄区域不包含目标。这些计数不是论文实验结果。", "locator": "合成网格设定", "status": "fixture", "url": None},
    {"id": "demo-limits", "kind": "paper", "title": "教学文档 · 讨论与边界", "page": 5, "quote": "候选数下降不能直接推出定位精度提高或实际运行时间同比下降。噪声、候选间相关性和粗定位偏差都会影响结果。此文档为产品交互演示而编写，不对应任何已发表论文。", "locator": "讨论", "status": "fixture", "url": None},
    {"id": "compare-method", "kind": "paper", "title": "对照教学文档 · 全域搜索", "page": 1, "quote": "对照方案始终保留全部 48 个候选位置。它避免区域裁剪带来的目标排除，但不保证最终恢复正确，也不消除噪声与模型误差。", "locator": "对照方法", "status": "fixture", "url": None},
]

NODES = [
    {"id": "problem", "title": "这篇内容在解决什么问题", "summary": "候选位置越多，需要比较的可能性就越多。能否利用已有的位置线索，把计算集中到更小的区域？", "paragraphs": ["我们先用一个合成的定位场景理解这个问题：观测告诉我们目标可能出现在什么地方，算法需要在候选位置中寻找解释。这里真正要权衡的是计算范围与真实目标的覆盖。"], "source_ids": ["demo-problem"], "concepts": ["candidate"], "kind": "narrative", "status": "fixture_ready"},
    {"id": "mechanism", "title": "缩小范围，为什么也可能漏掉目标", "summary": "更小的搜索空间意味着更少的候选，但前提是正确答案没有被排除。动手改变范围，观察这两个量如何一起变化。", "paragraphs": ["下面只演示候选裁剪与目标覆盖的关系，不模拟真实稀疏重建算法。枚举的候选数是计算量的粗略代理，不能据此推算论文算法的加速倍数。"], "source_ids": ["demo-method", "demo-evidence"], "concepts": ["candidate", "sparse"], "kind": "candidate_explorer", "status": "fixture_ready"},
    {"id": "formula", "title": "从网格回到公式：y = Ax + ε", "summary": "每个网格对应 x 的一个坐标，也对应 A 的一列。范围裁剪改变了允许出现的解。", "paragraphs": ["y 是实际观测，A 描述各个候选位置会产生怎样的观测，x 表示目标位置和强度，ε 是噪声。位置很少时，x 的非零分量也很少。", "只留下区域 S，就得到受约束的模型 y ≈ Aₛxₛ。若真实目标在 S 外，即使把局部优化做得很好，也无法用被保留的真实位置来表示它。"], "source_ids": ["demo-formula"], "concepts": ["sparse", "matrix"], "kind": "formula", "status": "fixture_ready"},
    {"id": "evidence", "title": "这个演示能说明什么", "summary": "全域 48 个候选，局部 16 个，极窄 4 个。候选数下降是真实计数，精度和速度提升没有在此测量。", "paragraphs": ["在这组教学设定里，局部区域仍保留真实位置，极窄区域则排除了它。这个现象展示了覆盖条件的作用，不是对某篇论文实验结果的复现。"], "source_ids": ["demo-evidence"], "concepts": [], "kind": "comparison", "status": "fixture_ready"},
    {"id": "limits", "title": "带着条件理解结论", "summary": "不是范围越小越好，而是利用可靠线索减少无关候选，同时保留真实解。", "paragraphs": ["粗定位有偏差时，局部区域可能选错；噪声较大或矩阵列相似时，覆盖真实位置也不保证恢复成功。", "回到实际论文，需要核对区域如何构造、噪声如何设定、比较基准是否一致，以及候选数量是否真的对应更低的运行成本。"], "source_ids": ["demo-limits"], "concepts": [], "kind": "narrative", "status": "fixture_ready"},
]

def fixture_documents():
    first = {"id": "adaptive-search", "title": "自适应搜索中的稀疏重建", "subtitle": "从搜索范围理解计算成本与目标覆盖", "authors": "paperMind 教学样例", "year": "2026", "type": "教学文档", "is_demo": True, "status": "demo_ready", "revision": 1, "nodes": deepcopy(NODES), "sources": deepcopy(SOURCES[:5]), "supplements": [], "attachments": [], "file_path": None, "page_count": 5}
    second = {"id": "global-search", "title": "全域搜索：保留全部候选", "subtitle": "用于跨文献比较的对照教学样例", "authors": "paperMind 教学样例", "year": "2026", "type": "对照文档", "is_demo": True, "status": "demo_ready", "revision": 1, "nodes": [{"id": "problem", "title": "保留全部候选，改变了什么", "summary": SOURCES[5]["quote"], "paragraphs": ["与区域裁剪对比时，先分清候选覆盖、恢复正确性和实际运行成本三个问题。已有概念可复用，但不同条件仍需解释。"], "source_ids": ["compare-method"], "concepts": ["candidate"], "kind": "narrative", "status": "fixture_ready"}], "sources": [deepcopy(SOURCES[5])], "supplements": [], "attachments": [], "file_path": None, "page_count": 1}
    return [first, second]

