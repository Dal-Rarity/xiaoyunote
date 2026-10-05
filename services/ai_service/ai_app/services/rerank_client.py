from loguru import logger

from ai_app.config import get_settings
from ai_app.deps import http

s = get_settings()


async def rerank(query: str, docs: list[str], top_n: int) -> list[tuple[int, float]]:
    """
    返回 [(原始索引, 相关性分数), ...]，按分数降序。
    失败时抛异常，由调用方决定是否降级。
    """
    if not docs:
        return []

    r = await http.post(
        f"{s.RERANK_BASE_URL}/rerank",
        headers={"Authorization": f"Bearer {s.RERANK_API_KEY}"},
        json={
            "model": s.RERANK_MODEL,
            "query": query,
            "documents": docs,
            "top_n": top_n,
        },
        timeout=10.0,
    )
    r.raise_for_status()
    data = r.json()
    return [(item["index"], item["relevance_score"]) for item in data["results"]]