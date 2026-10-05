import httpx
from qdrant_client import QdrantClient
from openai import AsyncOpenAI, OpenAI
from loguru import logger

from ai_app.config import get_settings


s = get_settings()

# 同步客户端（离线入库用）
qdrant_sync = QdrantClient(url=s.QDRANT_URL, api_key=s.QDRANT_API_KEY or None)

# 异步客户端（在线检索用）
qdrant = QdrantClient(url=s.QDRANT_URL, api_key=s.QDRANT_API_KEY or None)

# LLM（异步流式）
llm = AsyncOpenAI(
    api_key=s.LLM_API_KEY or "EMPTY",
    base_url=s.LLM_BASE_URL,
    timeout=s.LLM_TIMEOUT,
)

# Embedding（Ollama OpenAI 兼容）
ollama = AsyncOpenAI(
    api_key="ollama",
    base_url=s.EMBED_BASE_URL,
    timeout=10.0,
)

# 通用 HTTP（rerank 等）
http = httpx.AsyncClient(timeout=10.0)


async def warmup():
    """轻量校验依赖，失败记日志不阻塞启动（降级原则）"""
    try:
        qdrant_sync.get_collections()
        logger.info("Qdrant connected")
    except Exception as e:
        logger.warning(f"Qdrant not ready: {e}")

    try:
        await ollama.models.list()
        logger.info("Ollama connected")
    except Exception as e:
        logger.warning(f"Ollama not ready: {e}")