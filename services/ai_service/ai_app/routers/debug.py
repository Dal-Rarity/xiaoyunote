from fastapi import APIRouter, Query

from ai_app.services.retriever import retrieve

router = APIRouter(prefix="/api/ai/debug", tags=["debug"])


@router.get("/retrieve")
async def debug_retrieve(
    q: str = Query(..., min_length=1),
    user_id: int = Query(..., description="用户 ID，用于多用户隔离"),
    data_type: str | None = Query(None, description="article/collection/favorite/praise/comment"),
    category: str | None = Query(None, description="分类，如 影后观感"),
):
    """检索质量肉眼调试（仅开发期）"""
    result = await retrieve(q, user_id=user_id, data_type=data_type, category=category)
    return {
        "refused": result.refused,
        "debug": result.debug,
        "chunks": [
            {
                "article_id": c.article_id,
                "title": c.title,
                "category": c.category,
                "data_type": c.data_type,
                "vector_score": round(c.vector_score, 4),
                "rerank_score": round(c.rerank_score, 4),
                "text": c.text[:120],
            }
            for c in result.chunks
        ],
    }