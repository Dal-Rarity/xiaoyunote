"""
FastAPI 入口
- 启用结构化日志（必须在最前面 import）
- 装配 CORS、路由、lifespan warmup
"""
import ai_app.utils.logger  # noqa: F401  —— 启用 JSON 结构化日志（必须最早执行）

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_app.config import get_settings
from ai_app.routers import health, debug, chat

s = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时轻量校验依赖，失败记日志不阻塞启动"""
    from ai_app.deps import warmup
    await warmup()
    yield


app = FastAPI(title=s.SERVICE_NAME, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5000", "http://localhost:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由注册
app.include_router(health.router)   # GET /health, GET /metrics
app.include_router(debug.router)    # GET /api/ai/debug/retrieve
app.include_router(chat.router)     # POST /api/ai/chat/stream