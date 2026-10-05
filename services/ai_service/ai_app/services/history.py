"""
会话历史：Redis List 存储，滑窗最近 N 轮，TTL 24h
Key: ai:hist:{session_id}
fail-open: Redis 挂了不阻断问答
"""
import json
from loguru import logger

from ai_app.config import get_settings

s = get_settings()

_KEY = "ai:hist:{sid}"
_TTL = 86400  # 24h


def _client():
    import redis.asyncio as aioredis
    return aioredis.from_url(s.REDIS_URL, socket_connect_timeout=2)


async def append(session_id: str, role: str, content: str):
    """追加一条消息，并裁剪到最近 HISTORY_TURNS * 2 条"""
    try:
        r = _client()
        key = _KEY.format(sid=session_id)
        await r.rpush(key, json.dumps({"role": role, "content": content}, ensure_ascii=False))
        await r.ltrim(key, -s.HISTORY_TURNS * 2, -1)
        await r.expire(key, _TTL)
        await r.aclose()
    except Exception as e:
        logger.warning(f"history append failed (fail-open): {e}")


async def get(session_id: str) -> list[dict]:
    """读取最近 N 轮历史，格式 [{"role": "user", "content": "..."}, ...]"""
    try:
        r = _client()
        raw = await r.lrange(_KEY.format(sid=session_id), 0, -1)
        await r.aclose()
        return [json.loads(x) for x in raw]
    except Exception as e:
        logger.warning(f"history get failed (fail-open): {e}")
        return []


async def clear(session_id: str):
    try:
        r = _client()
        await r.delete(_KEY.format(sid=session_id))
        await r.aclose()
    except Exception as e:
        logger.warning(f"history clear failed: {e}")