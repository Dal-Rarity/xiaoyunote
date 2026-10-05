"""
一键同步：MySQL → 分块 → 向量化 → Qdrant
覆盖：article / collection / favorite / praise / comment
幂等：先按 (user_id, data_type) 删除旧点，再插入
"""
import asyncio
import os
import sys
from urllib.parse import urlparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, ".env"))

import pymysql
from ai_app.config import get_settings
from ai_app.services.chunker import chunk_article, chunk_behavior
from ai_app.services.embedding_client import embed_texts
from ai_app.services.vector_store import (
    ensure_collection,
    upsert_chunks,
    count_points,
)

s = get_settings()


def _dsn_to_kwargs(dsn):
    u = urlparse(dsn)
    charset = "utf8mb4"
    if "charset=" in (u.query or ""):
        charset = dict(p.split("=", 1) for p in u.query.split("&")).get("charset", charset)
    return dict(
        host=u.hostname,
        port=u.port or 3306,
        user=u.username,
        password=u.password or "",
        database=u.path.lstrip("/"),
        charset=charset,
    )


DB = _dsn_to_kwargs(s.MYSQL_DSN)


def conn():
    return pymysql.connect(**DB)


def fetch_articles():
    c = conn(); cur = c.cursor()
    cur.execute("""
        SELECT article_id, user_id, title, article_content, label_name, article_tag, create_time
        FROM article WHERE drafted = 1
    """)
    rows = []
    for aid, uid, title, body, cat, tags, created in cur.fetchall():
        rows.append({
            "article_id": aid, "user_id": uid, "title": title,
            "content": body or "", "category": cat or "未分类",
            "tags": [t.strip() for t in (tags or "").split(",") if t.strip()],
            "created_at": str(created),
        })
    c.close()
    return rows


def fetch_behavior(table: str, data_type: str, has_canceled: bool = True,
                   extra_col: str | None = None, pk_col: str = "id"):
    c = conn(); cur = c.cursor()
    extra_sel = f", t.{extra_col}" if extra_col else ", ''"
    where = "WHERE a.drafted = 1 AND t.canceled = 0" if has_canceled else "WHERE a.drafted = 1"
    sql = f"""
        SELECT t.{pk_col}, t.user_id, t.article_id, a.title, a.label_name, t.create_time {extra_sel}
        FROM {table} t
        LEFT JOIN article a ON a.article_id = t.article_id
        {where}
    """
    cur.execute(sql)
    rows = []
    for pk, uid, aid, title, cat, created, extra in cur.fetchall():
        rows.append({
            "source_id": pk,
            "user_id": uid, "article_id": aid, "title": title or "",
            "category": cat or "", "created_at": str(created), "extra": extra or "",
        })
    c.close()
    return rows


async def main():
    ensure_collection(recreate=True)
    print(f"Collection ready: {s.QDRANT_COLLECTION}")

    articles = fetch_articles()
    print(f"Fetched {len(articles)} articles")
    chunks = []
    for a in articles:
        chunks.extend(chunk_article(a))

    for table, dtype, has_canceled, extra_col, pk_col in [
        ("collection", "collection", True, None, "collection_id"),
        ("favorite", "favorite", True, None, "favorite_id"),
        ("praise", "praise", True, None, "praise_id"),
        ("comment", "comment", False, "content", "comment_id"),
    ]:
        try:
            rows = fetch_behavior(table, dtype, has_canceled, extra_col, pk_col)
            print(f"Fetched {len(rows)} {dtype}")
            for row in rows:
                chunks.extend(chunk_behavior(row, dtype))
        except Exception as e:
            print(f"[skip] {table}: {e}")

    print(f"Total chunks: {len(chunks)}")

    if chunks:
        texts = [c.text for c in chunks]
        vectors = await embed_texts(texts)
        upsert_chunks(chunks, vectors)

    print(f"Qdrant points: {count_points()}")

    # 清缓存（双保险，指纹含 chunk_id 本就失效）
    try:
        import redis as redis_sync
        r = redis_sync.from_url(s.REDIS_URL, socket_connect_timeout=2)
        keys = list(r.scan_iter("ai:cache:*"))
        if keys:
            r.delete(*keys)
            print(f"Cleared {len(keys)} cache keys")
    except Exception as e:
        print(f"[warn] cache clear skipped: {e}")


if __name__ == "__main__":
    asyncio.run(main())