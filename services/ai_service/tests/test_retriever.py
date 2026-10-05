import pytest
from unittest.mock import AsyncMock, patch

from ai_app.services.retriever import retrieve


@pytest.mark.asyncio
async def test_empty_recall_refused():
    with patch("ai_app.services.retriever.embed_texts", new=AsyncMock(return_value=[[0.0] * 1024])), \
         patch("ai_app.services.retriever.qdrant") as mock_q:
        mock_q.search.return_value = []
        r = await retrieve("test", user_id=1)
        assert r.refused is True


@pytest.mark.asyncio
async def test_rerank_fail_open():
    """Rerank 失败时降级为向量分排序，不报错"""
    fake_hit = type("H", (), {
        "id": "x",
        "score": 0.5,
        "payload": {
            "article_id": 1, "title": "t", "text": "text",
            "category": "日记", "tags": [], "data_type": "article",
        },
    })()

    with patch("ai_app.services.retriever.embed_texts", new=AsyncMock(return_value=[[0.0] * 1024])), \
         patch("ai_app.services.retriever.qdrant") as mock_q, \
         patch("ai_app.services.retriever.rerank", new=AsyncMock(side_effect=Exception("network"))):
        mock_q.search.return_value = [fake_hit]
        r = await retrieve("test", user_id=1)
        assert r.refused is False
        assert r.chunks[0].rerank_score == 0.5


@pytest.mark.asyncio
async def test_threshold_filter():
    """分数低于阈值应被过滤"""
    fake_hit = type("H", (), {
        "id": "x",
        "score": 0.01,
        "payload": {
            "article_id": 1, "title": "t", "text": "text",
            "category": "日记", "tags": [], "data_type": "article",
        },
    })()

    with patch("ai_app.services.retriever.embed_texts", new=AsyncMock(return_value=[[0.0] * 1024])), \
         patch("ai_app.services.retriever.qdrant") as mock_q, \
         patch("ai_app.services.retriever.rerank", new=AsyncMock(return_value=[(0, 0.01)])):
        mock_q.search.return_value = [fake_hit]
        r = await retrieve("test", user_id=1, threshold=0.2)
        assert r.refused is True