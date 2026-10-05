"""
问答管线：历史 → 检索（意图识别）→ 拒答判断 → 缓存 → 生成 → sources → 写历史
产出事件流：sources / delta / refused / done / error
每问一条 qa_done 日志 + 指标累加
"""
import asyncio
import time
import uuid

from loguru import logger

from ai_app.config import get_settings
from ai_app.services import cache, history, metrics
from ai_app.services.llm_client import stream_chat
from ai_app.services.prompts import build_messages
from ai_app.services.retriever import retrieve

s = get_settings()


# ============ 意图识别 ============
def detect_data_type(question: str) -> str | None:
    if "收藏" in question:
        return "collection"
    if "喜欢" in question:
        return "favorite"
    if "点赞" in question:
        return "praise"
    if "评论" in question:
        return "comment"
    return None   # 默认混合检索


# ============ 主流程 ============
async def stream_answer(
    question: str,
    user_id: int,
    session_id: str | None = None,
    data_type: str | None = None,
    category: str | None = None,
):
    trace_id = uuid.uuid4().hex[:12]
    t0 = time.time()
    refused = False
    cache_hit = False
    error = False
    recall = 0
    kept = 0
    top_score = 0.0

    # 0. 意图识别（如未显式指定 data_type）
    if data_type is None:
        data_type = detect_data_type(question)

    # 1. 读历史
    hist = await history.get(session_id) if session_id else []

    # 2. 检索
    r = await retrieve(
        question,
        user_id=user_id,
        data_type=data_type,
        category=category,
    )
    recall = r.debug.get("recall", 0)
    kept = r.debug.get("kept", 0)
    if r.chunks:
        top_score = max(c.rerank_score for c in r.chunks)

    # 3. 检索层拒答短路
    if r.refused:
        refused = True
        elapsed = int((time.time() - t0) * 1000)
        logger.bind(
            trace_id=trace_id, user_id=user_id, question=question[:50],
            elapsed_ms=elapsed, recall=recall, kept=0, top_score=0.0,
            cache_hit=False, refused=True, error=False,
            data_type=data_type, event="qa_done",
        ).info("qa_done")
        metrics.record(elapsed, refused=True)

        yield {"type": "refused", "text": s.REFUSE_MESSAGE}
        if session_id:
            await history.append(session_id, "user", question)
            await history.append(session_id, "assistant", s.REFUSE_MESSAGE)
        return

    # 4. 先发 sources
    yield {
        "type": "sources",
        "items": [
            {
                "article_id": c.article_id,
                "title": c.title,
                "category": c.category,
                "data_type": c.data_type,
                "score": round(max(c.rerank_score, c.vector_score), 4),
            }
            for c in r.chunks
        ],
    }

    # 5. 缓存查询
    chunk_ids = [c.point_id for c in r.chunks]
    cached = await cache.get_answer(question, chunk_ids)

    if cached:
        cache_hit = True
        # 缓存内容可能是 LLM 层拒答
        llm_refused = cached.strip().startswith(s.REFUSE_MESSAGE[:10])

        # 模拟流式
        for i in range(0, len(cached), 10):
            yield {"type": "delta", "text": cached[i : i + 10]}
            await asyncio.sleep(0)

        elapsed = int((time.time() - t0) * 1000)
        logger.bind(
            trace_id=trace_id, user_id=user_id, question=question[:50],
            elapsed_ms=elapsed, recall=recall, kept=kept, top_score=top_score,
            cache_hit=True, refused=llm_refused, error=False,
            data_type=data_type, event="qa_done",
        ).info("qa_done")
        metrics.record(elapsed, refused=llm_refused, cache_hit=True)

        if session_id:
            await history.append(session_id, "user", question)
            await history.append(session_id, "assistant", cached)
        return

    # 6. 正常生成
    messages = build_messages(question, r.chunks, hist)
    full_parts: list[str] = []

    try:
        async for delta in stream_chat(messages):
            full_parts.append(delta)
            yield {"type": "delta", "text": delta}
    except Exception as e:
        error = True
        logger.exception(f"llm stream failed: {e}")
        yield {
            "type": "error",
            "code": type(e).__name__,
            "message": "服务暂时不可用，请重试",
        }
        elapsed = int((time.time() - t0) * 1000)
        logger.bind(
            trace_id=trace_id, user_id=user_id, question=question[:50],
            elapsed_ms=elapsed, recall=recall, kept=kept, top_score=top_score,
            cache_hit=False, refused=False, error=True,
            data_type=data_type, event="qa_done",
        ).info("qa_done")
        metrics.record(elapsed, error=True)
        return

    # 7. 写缓存 + 写历史 + 记录指标
    full_answer = "".join(full_parts)

    # 检测 LLM 层拒答（模型输出固定话术）
    llm_refused = full_answer.strip().startswith(s.REFUSE_MESSAGE[:10])

    if full_answer:
        await cache.set_answer(question, chunk_ids, full_answer)
    if session_id:
        await history.append(session_id, "user", question)
        await history.append(session_id, "assistant", full_answer)

    elapsed = int((time.time() - t0) * 1000)
    logger.bind(
        trace_id=trace_id, user_id=user_id, question=question[:50],
        elapsed_ms=elapsed, recall=recall, kept=kept, top_score=top_score,
        cache_hit=False, refused=llm_refused, error=False,
        data_type=data_type, event="qa_done",
    ).info("qa_done")
    metrics.record(elapsed, refused=llm_refused)