from dataclasses import dataclass, field
from loguru import logger
from qdrant_client import models

from ai_app.config import get_settings
from ai_app.deps import qdrant
from ai_app.services.embedding_client import embed_texts
from ai_app.services.rerank_client import rerank

s = get_settings()


@dataclass
class RetrievedChunk:
    point_id: str
    article_id: int
    title: str
    text: str
    category: str
    tags: list[str]
    data_type: str
    vector_score: float = 0.0
    rerank_score: float = 0.0


@dataclass
class RetrieveResult:
    chunks: list[RetrievedChunk] = field(default_factory=list)
    refused: bool = False
    debug: dict = field(default_factory=dict)


async def retrieve(
    question: str,
    user_id: int,
    data_type: str | None = None,
    category: str | None = None,
    recall_top_k: int | None = None,
    rerank_top_n: int | None = None,
    threshold: float | None = None,
) -> RetrieveResult:
    """
    两阶段检索：向量召回 → Rerank → 阈值过滤 → 拒答
    - user_id 强制过滤（多用户隔离）
    - data_type/category 可选过滤（行为数据查询）
    """
    recall_top_k = recall_top_k or s.RECALL_TOP_K
    rerank_top_n = rerank_top_n or s.RERANK_TOP_N
    threshold = threshold if threshold is not None else s.SCORE_THRESHOLD

    # 1. 问题向量化
    vectors = await embed_texts([question])
    qvec = vectors[0]

    # 2. Qdrant 召回（带 user_id 过滤）
    must = [
        models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))
    ]
    if data_type:
        must.append(
            models.FieldCondition(key="data_type", match=models.MatchValue(value=data_type))
        )
    if category:
        must.append(
            models.FieldCondition(key="category", match=models.MatchValue(value=category))
        )

    hits = qdrant.search(
        collection_name=s.QDRANT_COLLECTION,
        query_vector=qvec,
        query_filter=models.Filter(must=must),
        limit=recall_top_k,
        with_payload=True,
    )

    if not hits:
        return RetrieveResult(refused=True, debug={"recall": 0, "kept": 0})

    # 3. Rerank（fail-open）
    docs = [h.payload["text"] for h in hits]
    try:
        ranked = await rerank(question, docs, rerank_top_n)
        ranked_chunks = []
        for idx, score in ranked:
            h = hits[idx]
            ranked_chunks.append(
                RetrievedChunk(
                    point_id=str(h.id),
                    article_id=h.payload["article_id"],
                    title=h.payload["title"],
                    text=h.payload["text"],
                    category=h.payload.get("category", ""),
                    tags=h.payload.get("tags", []),
                    data_type=h.payload["data_type"],
                    vector_score=h.score,
                    rerank_score=score,
                )
            )
        rerank_used = True
    except Exception as e:
        logger.warning(f"rerank failed, fallback to vector score: {e}")
        ranked_chunks = [
            RetrievedChunk(
                point_id=str(h.id),
                article_id=h.payload["article_id"],
                title=h.payload["title"],
                text=h.payload["text"],
                category=h.payload.get("category", ""),
                tags=h.payload.get("tags", []),
                data_type=h.payload["data_type"],
                vector_score=h.score,
                rerank_score=h.score,
            )
            for h in hits[:rerank_top_n]
        ]
        rerank_used = False

    # 4. 阈值过滤（取 max(rerank, vector)）
    kept = [
        c for c in ranked_chunks
        if max(c.rerank_score, c.vector_score) >= threshold
    ]

    if not kept:
        return RetrieveResult(
            refused=True,
            debug={"recall": len(hits), "kept": 0, "rerank_used": rerank_used},
        )

    return RetrieveResult(
        chunks=kept,
        refused=False,
        debug={"recall": len(hits), "kept": len(kept), "rerank_used": rerank_used},
    )