"""
系统提示词与 context 拼装
内容来自 T8 冻结版 prompt-system-v1（身份修正后）
"""
from ai_app.config import get_settings

s = get_settings()

SYSTEM_PROMPT = """你是「小语手记」站点的AI助手，基于博主的真实文章回答问题。你不是博主本人，而是帮助博主回顾他自己文章的工具。

规则：
1. 只使用【参考资料】中的信息作答，不得使用你自己的知识补全。
2. 若参考资料中没有答案，必须原样回复：「{refuse}」——不要试图猜测。
3. 回答中凡使用到某条资料，用[1][2]这样的上标标注，编号与资料编号一致。
4. 语气自然、口语化，像是在帮博主回忆他写过的东西；用“你”称呼博主，说“你的文章”而不是“我的文章”；不要说“根据参考资料”。
5. 回答控制在300字以内，除非用户明确要求展开。
6. 涉及日期、书名、片名时，必须与资料完全一致，不得改写。

【参考资料】
{context}
"""


def build_context(chunks) -> str:
    """
    给每条资料固定编号 [1] [2] [3]...
    chunks: list[RetrievedChunk]
    """
    if not chunks:
        return "（无参考资料）"

    lines = []
    for i, c in enumerate(chunks, start=1):
        # 元数据头已在 chunk 里，这里再补一层来源标识
        lines.append(f"[{i}] 来源：《{c.title}》｜分类：{c.category}")
        lines.append(c.text)
        lines.append("")  # 空行分隔

    return "\n".join(lines)


def build_messages(question: str, chunks, history: list[dict] | None = None) -> list[dict]:
    """拼装最终送给 LLM 的 messages"""
    context = build_context(chunks)
    system_content = SYSTEM_PROMPT.format(
        refuse=s.REFUSE_MESSAGE,
        context=context,
    )

    messages = [{"role": "system", "content": system_content}]

    # 历史轮数截断
    if history:
        messages.extend(history[-s.HISTORY_TURNS * 2:])

    messages.append({"role": "user", "content": question})
    return messages