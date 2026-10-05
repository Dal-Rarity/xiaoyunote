import json
import time

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from loguru import logger

from ai_app.config import get_settings
from ai_app.models.schemas import ChatRequest
from ai_app.services.chat_pipeline import stream_answer

s = get_settings()
router = APIRouter(prefix="/api/ai", tags=["chat"])


def sse(event: str, data: dict) -> bytes:
    """SSE 帧：event + data + 两个换行"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n".encode("utf-8")


async def verify_internal(x_internal_token: str = Header(default="")):
    """内部 Token 校验；INTERNAL_TOKEN 为空则跳过（仅本地开发）"""
    if s.INTERNAL_TOKEN and x_internal_token != s.INTERNAL_TOKEN:
        raise HTTPException(status_code=401, detail="invalid internal token")


@router.post("/chat/stream")
async def chat_stream(
    req: ChatRequest,
    request: Request,
    x_user_id: str = Header(default="0"),
    _=Depends(verify_internal),
):
    """
    浏览器 → Flask 网关 → 本接口
    事件序列：sources → delta* → done → [DONE]
    拒答：refused → done → [DONE]
    """
    try:
        user_id = int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="invalid user id")

    async def gen():
        t0 = time.time()
        try:
            async for item in stream_answer(req.question, user_id=user_id, session_id=req.session_id):
                # 客户端断开 → 停止生成，省钱省 GPU
                if await request.is_disconnected():
                    logger.info(f"client disconnected, cancel generation session_id={req.session_id}")
                    return
                yield sse(item["type"], item)

            yield sse("done", {"elapsed_ms": int((time.time() - t0) * 1000)})

        except Exception as e:
            logger.exception("chat stream error")
            yield sse("error", {
                "code": type(e).__name__,
                "message": "服务暂时不可用，请重试",
            })

        finally:
            yield b"data: [DONE]\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁 Nginx 缓冲
        },
    )