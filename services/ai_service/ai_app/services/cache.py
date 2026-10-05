"""
检索感知缓存
Key: ai:cache:{fingerprint}
fingerprint = sha256(question + sorted(chunk_ids))
语料一变 → chunk_id 变 → 指纹变 → 自动失效
fail-open: Redis 挂了照常问答
"""
import hashlib
from loguru import logger

from ai_app.config import get_settings

s = get_settings()


def _client():
    import redis.asyncio as aioredis
    return aioredis.from_url(s.REDIS_URL, socket_connect_timeout=2)


def fingerprint(question: str, chunk_ids: list[str]) -> str:
    raw = question.strip().lower() + "|" + "|".join(sorted(chunk_ids))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


async def get_answer(question: str, chunk_ids: list[str]) -> str | None:
    if not s.CACHE_ENABLED:
        return None
    try:
        r = _client()
        val = await r.get(f"ai:cache:{fingerprint(question, chunk_ids)}")
        await r.aclose()
        return val.decode("utf-8") if val else None
    except Exception as e:
        logger.warning(f"cache get failed (fail-open): {e}")
        return None


async def set_answer(question: str, chunk_ids: list[str], answer: str):
    if not s.CACHE_ENABLED:
        return
    try:
        r = _client()
        await r.set(
            f"ai:cache:{fingerprint(question, chunk_ids)}",
            answer.encode("utf-8"),
            ex=s.CACHE_TTL,
        )
        await r.aclose()
    except Exception as e:
        logger.warning(f"cache set failed (fail-open): {e}")


async def clear_all():
    """同步语料后主动清缓存（双保险）"""
    try:
        r = _client()
        keys = [k async for k in r.scan_iter("ai:cache:*")]
        if keys:
            await r.delete(*keys)
        await r.aclose()
        return len(keys)
    except Exception as e:
        logger.warning(f"cache clear failed: {e}")
        return 0