"""Deterministic demo provider. Never masquerades as an LLM or web retrieval."""
from .contracts import DemoAction

SCOPE_TEXT = {"all": "全域", "local": "局部", "narrow": "极窄"}

def reply(document, text):
    """The live provider will implement this contract; fixtures only cover known intents."""
    result = {"provider": "fixture", "source_ids": [], "action": None, "memory": None, "can_patch": True}
    if not document["is_demo"]:
        return {**result, "text": "这份 PDF 已在本地抽取文本，但当前 Demo 没有接入大模型，不能为它生成可靠解释。你可以查看原文与抽取结果；体验完整阅读流程请切换到教学样例。", "can_patch": False}
    if any(s in text for s in ["比较", "对比", "另一篇", "全域搜索"]):
        if "global-search" not in document["attachments"] or document["id"] != "adaptive-search":
            return {**result, "text": "要比较两份内容，请先点「附加文献」选择对照教学文档。当前回答不会把未附加文档当作已读取的来源。", "can_patch": False}
        return {**result, "text": "两份教学文档比较的是候选覆盖。自适应方案先裁剪区域，只在覆盖真实目标的前提下减少候选；全域方案保留全部候选，避免区域裁剪造成的直接排除。两者都不能仅凭覆盖条件保证最终恢复正确。这里没有运行任何论文实验，也没有证明实际加速比例。", "source_ids": ["demo-method", "compare-method"]}
    if any(s in text for s in ["缩小", "调小", "极窄", "演示", "恢复范围", "全域"]):
        if document["id"] != "adaptive-search":
            return {**result, "text": "当前对照文档没有可操作的搜索演示。请打开「自适应搜索中的稀疏重建」体验此操作。", "can_patch": False}
        scope = "all" if any(s in text for s in ["恢复范围", "全域"]) else "narrow"
        action = DemoAction(type="set_search_scope", scope=scope, node_id="mechanism").model_dump()
        return {**result, "text": f"我把教学演示切换到{SCOPE_TEXT[scope]}范围。" + ("现在只保留 4 个候选，真实目标落在区域外。即使局部求解非常准确，也无法找回一开始就被排除的位置。这说明裁剪的前提是覆盖真实目标。" if scope == "narrow" else "现在保留全部 48 个候选，真实位置重新进入候选集合。保留真实位置仍不保证最终恢复正确。") + "你可以点击演示中的「恢复上一步」。", "source_ids": ["demo-method", "demo-evidence"], "action": action}
    if any(s in text for s in ["符号", "公式", "矩阵", "Ax", "推导"]):
        return {**result, "text": "先按符号看：y 是测量结果，x 是各候选位置的强度，A 的每一列描述一个位置会怎样影响测量，ε 是噪声。缩小候选区域，就是只让 x 的一部分坐标可能非零。如果真实目标对应的坐标被删去，剩余模型就无法用那个真实位置解释观测。这里是直觉说明，没有证明任意矩阵都能稳定恢复稀疏信号。", "source_ids": ["demo-formula"], "memory": {"id": "symbol-preference", "text": "解释公式时优先逐一说明符号", "kind": "explanation_preference"}}
    if any(s in text for s in ["稀疏", "非零"]):
        return {**result, "text": "此处稀疏是指：在许多候选位置中，只有少数位置真的有目标，所以位置强度向量 x 只有少数非零分量。它并不是说信号很弱。还要注意，稀疏只是恢复问题的一项条件，矩阵、噪声和目标数量也会影响能否恢复。", "source_ids": ["demo-formula"]}
    if any(s in text for s in ["可靠", "反例", "争议", "评议"]):
        return {**result, "text": "这一请求需要检索外部研究进行评议。当前 Demo 未接入联网检索或大模型，不能给出真实的学术可靠性评价。教学文档自身已明确：候选覆盖不等于恢复成功，候选数也不等于运行耗时。", "source_ids": ["demo-limits"], "can_patch": False}
    if any(s in text for s in ["为什么", "候选", "漏", "条件", "范围", "解释"]):
        return {**result, "text": "缩小范围只减少了算法要考虑的候选，不会凭空增加信息。它有效的前提是区域仍覆盖真实目标；一旦目标在区域外，后续局部搜索就没有正确位置可选。即使覆盖目标，噪声和候选之间的相似性仍可能让恢复失败。回到主线时，应把「减少候选」与「保证精度」分开理解。", "source_ids": ["demo-method", "demo-limits"]}
    return {**result, "text": "当前是预设回答 Demo，暂不具备自由问答能力。可以试试「为什么范围缩小会漏掉目标」「把范围缩小演示一下」「逐一解释公式符号」，或附加对照文档后问「比较两篇方法」。", "can_patch": False}
