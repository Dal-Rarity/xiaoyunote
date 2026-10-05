import pytest
from unittest.mock import AsyncMock, patch

from ai_app.services import chat_pipeline


@pytest.mark.asyncio
async def test_normal_stream():
    """正常流：sources → delta → 结束"""
    from ai_app.services.retriever import RetrieveResult, RetrievedChunk

    fake_chunks = [
        RetrievedChunk(
            point_id="x1", article_id=75, title="三体", text="正文",
            category="阅读笔记", tags=[], data_type="article",
            vector_score=0.8, rerank_score=0.85,
        )
    ]
    fake_result = RetrieveResult(chunks=fake_chunks, refused=False, debug={})

    async def fake_stream(messages):
        yield "你好"
        yield "世界"

    with patch("ai_app.services.chat_pipeline.retrieve", new=AsyncMock(return_value=fake_result)), \
         patch("ai_app.services.chat_pipeline.stream_chat", new=fake_stream):
        events = []
        async for ev in chat_pipeline.stream_answer("问题", user_id=1):
            events.append(ev)

    types = [e["type"] for e in events]
    assert types[0] == "sources"
    assert "delta" in types
    assert events[0]["items"][0]["article_id"] == 75


@pytest.mark.asyncio
async def test_refused_short_circuit():
    """拒答短路：不调 LLM"""
    from ai_app.services.retriever import RetrieveResult

    fake_result = RetrieveResult(chunks=[], refused=True, debug={})

    with patch("ai_app.services.chat_pipeline.retrieve", new=AsyncMock(return_value=fake_result)), \
         patch("ai_app.services.chat_pipeline.stream_chat") as mock_llm:
        events = []
        async for ev in chat_pipeline.stream_answer("天气", user_id=1):
            events.append(ev)

        assert len(events) == 1
        assert events[0]["type"] == "refused"
        mock_llm.assert_not_called()   # 关键断言


@pytest.mark.asyncio
async def test_main_model_fail_fallback():
    """主模型失败切备选"""
    from ai_app.services.llm_client import stream_chat
    from ai_app.deps import llm

    call_count = {"n": 0}

    class FakeChoice:
        class delta:
            content = "备选回答"

    class FakeChunk:
        choices = [FakeChoice]

    class FakeStream:
        def __aiter__(self):
            return self
        async def __anext__(self):
            if call_count["n"] == 0:
                call_count["n"] = 1
                return FakeChunk
            raise StopAsyncIteration

    async def fake_create(*args, **kwargs):
        if kwargs.get("model") == "qwen3.8-flash":
            raise Exception("429 rate limit")
        return FakeStream()

    with patch.object(llm.chat.completions, "create", new=fake_create):
        result = []
        async for delta in stream_chat([{"role": "user", "content": "test"}]):
            result.append(delta)
        assert result == ["备选回答"]