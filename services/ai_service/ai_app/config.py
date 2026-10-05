from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ========== 服务 ==========
    SERVICE_NAME: str = "xiaoyunote-ai"
    INTERNAL_TOKEN: str = ""  # 网关→AI 内部鉴权；空则不校验（仅本地开发允许）

    # ========== Embedding（本地 Ollama，与 FastAPI 同在 Windows） ==========
    EMBED_BASE_URL: str = "http://127.0.0.1:11434/v1"
    EMBED_MODEL: str = "bge-m3"
    EMBED_DIM: int = 1024
    EMBED_BATCH: int = 16

    # ========== Rerank（硅基流动免费档） ==========
    RERANK_BASE_URL: str = "https://api.siliconflow.cn/v1"
    RERANK_MODEL: str = "BAAI/bge-reranker-v2-m3"
    RERANK_API_KEY: str = ""

    # ========== LLM（通义 OpenAI 兼容模式，T10 冻结：qwen3.8-flash） ==========
    LLM_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    LLM_MODEL: str = "qwen3.8-flash"
    LLM_FALLBACK_MODEL: str = "deepseek-chat"
    LLM_API_KEY: str = ""
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKEN: int = 1024
    LLM_TIMEOUT: float = 60.0

    # ========== 向量库（Qdrant 在虚拟机） ==========
    QDRANT_URL: str = "http://192.168.56.200:6333"
    QDRANT_COLLECTION: str = "xiaoyunote_articles"
    QDRANT_API_KEY: str = ""

    # ========== 检索（params-frozen-v1） ==========
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 50
    RECALL_TOP_K: int = 15        # 实验 C 结论
    RERANK_TOP_N: int = 5
    SCORE_THRESHOLD: float = 0.2  # 实验 B 结论
    REFUSE_MESSAGE: str = "这个问题在我的笔记里没有找到相关内容，我只能回答和我站点文章有关的问题。"

    # ========== 会话与缓存（Redis 在虚拟机） ==========
    REDIS_URL: str = "redis://192.168.56.200:6379/0"
    HISTORY_TURNS: int = 3
    CACHE_TTL: int = 3600
    CACHE_ENABLED: bool = True

    # ========== 多用户隔离 ==========
    USER_ISOLATION_ENABLED: bool = True  # T13 检索按 user_id 过滤

    # ========== 主站数据库（只读，语料同步用；连接串仅允许从 .env 注入） ==========
    MYSQL_DSN: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()