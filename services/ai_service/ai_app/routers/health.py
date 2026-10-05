from fastapi import APIRouter

from ai_app.config import get_settings
from ai_app.deps import qdrant_sync
from ai_app.services import metrics

router = APIRouter()
s = get_settings()


def _probe_qdrant() -> str:
    try:
        qdrant_sync.get_collections()
        return "up"
    except Exception:
        return "down"


def _probe_redis() -> str:
    try:
        import redis
        r = redis.from_url(s.REDIS_URL, socket_connect_timeout=2)
        r.ping()
        return "up"
    except Exception:
        return "down"


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "service": s.SERVICE_NAME,
        "qdrant": _probe_qdrant(),
        "redis": _probe_redis(),
        "llm": "configured" if s.LLM_API_KEY else "missing",
    }


@router.get("/metrics")
async def metrics_endpoint():
    """聚合指标（只暴露聚合值，不泄露隐私）"""
    return metrics.snapshot()