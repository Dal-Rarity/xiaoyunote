import uuid
from qdrant_client import models

from ai_app.config import get_settings
from ai_app.deps import qdrant_sync
from ai_app.models.dto import Chunk

s = get_settings()

_NS = uuid.uuid5(uuid.NAMESPACE_URL, "https://xiaoyunote.local/corpus")


def point_id(user_id: int, data_type: str, article_id: int, idx: int, source_id: int = 0) -> str:
    """确定性 ID；行为数据用 source_id 区分同用户同文章的多条记录"""
    raw = f"{user_id}:{data_type}:{article_id}:{source_id}:{idx}"
    return str(uuid.uuid5(_NS, raw))

def ensure_collection(recreate: bool = False):
    if recreate:
        qdrant_sync.recreate_collection(
            s.QDRANT_COLLECTION,
            vectors_config=models.VectorParams(
                size=s.EMBED_DIM, distance=models.Distance.COSINE
            ),
        )
    else:
        existing = {c.name for c in qdrant_sync.get_collections().collections}
        if s.QDRANT_COLLECTION not in existing:
            qdrant_sync.create_collection(
                s.QDRANT_COLLECTION,
                vectors_config=models.VectorParams(
                    size=s.EMBED_DIM, distance=models.Distance.COSINE
                ),
            )


def upsert_chunks(chunks: list[Chunk], vectors: list[list[float]]):
    if not chunks:
        return
    points = []
    for c, v in zip(chunks, vectors):
        pid = c.point_id or point_id(c.user_id, c.data_type, c.article_id, c.chunk_index, c.source_id)
        c.point_id = pid
        points.append(
            models.PointStruct(
                id=pid,
                vector=v,
                payload={
                    "user_id": c.user_id,
                    "data_type": c.data_type,
                    "article_id": c.article_id,
                    "title": c.title,
                    "chunk_index": c.chunk_index,
                    "text": c.text,
                    "category": c.category,
                    "tags": c.tags,
                    "created_at": c.created_at,
                },
            )
        )
    qdrant_sync.upsert(s.QDRANT_COLLECTION, points=points, wait=True)


def delete_by_user(user_id: int, data_type: str | None = None):
    """删旧点（幂等 + 重同步）"""
    must = [
        models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))
    ]
    if data_type:
        must.append(
            models.FieldCondition(key="data_type", match=models.MatchValue(value=data_type))
        )
    qdrant_sync.delete(
        s.QDRANT_COLLECTION,
        points_selector=models.FilterSelector(filter=models.Filter(must=must)),
    )


def count_points() -> int:
    return qdrant_sync.count(s.QDRANT_COLLECTION).count