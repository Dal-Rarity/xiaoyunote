"""
Flask AI 网关 + 问答页路由
- POST /api/ai/chat/stream  网关：鉴权 + 注入身份 + 转发 SSE
- GET  /ai                  问答页模板
主站零侵入（蓝图模式）
"""
import os

import httpx
from flask import (
    Blueprint, Response, jsonify, render_template, request,
    session, stream_with_context, redirect,
)

ai = Blueprint("ai", __name__)


def _load_env_file(path: str) -> dict:
    """手动解析 .env（跳过注释、空行、引号）"""
    result = {}
    if not os.path.exists(path):
        return result
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            result[k.strip()] = v.strip().strip('"').strip("'")
    return result


# 读 FastAPI 的 .env（唯一可信源）
_AI_ENV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "services", "ai_service", ".env",
)
_env = _load_env_file(_AI_ENV_PATH)

# 优先级：进程环境变量（Docker 部署，镜像内不含 services/ai_service/.env）> .env 文件（本地开发）
AI_BASE = (
    os.getenv("AI_SERVICE_URL")
    or _env.get("AI_SERVICE_URL")
    or "http://127.0.0.1:8100"
)
AI_INTERNAL_TOKEN = (
    os.getenv("AI_INTERNAL_TOKEN")
    or os.getenv("INTERNAL_TOKEN")
    or _env.get("INTERNAL_TOKEN", "")
)

# 临时调试
# print("DEBUG env path:", _AI_ENV_PATH)
# print("DEBUG AI_BASE:", repr(AI_BASE))
# print("DEBUG AI_INTERNAL_TOKEN:", repr(AI_INTERNAL_TOKEN))

# 模块级单例，复用连接池
_client = httpx.Client(timeout=None)


# ================= T17 网关 =================
@ai.post("/api/ai/chat/stream")
def chat_stream():
    # print("DEBUG session:", dict(session))
    # 1. 校验登录态（与主站 personal.py 一致）
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "unauthorized"}), 401

    # 2. 参数校验
    body = request.get_json(silent=True) or {}
    q = (body.get("question") or "").strip()
    sid = (body.get("session_id") or "").strip()

    if not q or len(q) > 500:
        return jsonify({"error": "invalid question"}), 422
    if not sid or len(sid) < 8 or len(sid) > 64:
        return jsonify({"error": "invalid session_id"}), 422

    # 3. 注入身份与 Token
    headers = {
        "Content-Type": "application/json",
        "X-Internal-Token": AI_INTERNAL_TOKEN,
        "X-User-Id": str(user_id),
        "Accept": "text/event-stream",
    }

    try:
        req = _client.build_request(
            "POST",
            f"{AI_BASE}/api/ai/chat/stream",
            json={"question": q, "session_id": sid},
            headers=headers,
        )
        r = _client.send(req, stream=True)

        if r.status_code != 200:
            r.close()
            return jsonify({"error": "ai service error"}), r.status_code

        return Response(
            stream_with_context(r.iter_bytes()),
            content_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "X-Accel-Buffering": "no",
            },
        )
    except httpx.HTTPError:
        return jsonify({"error": "ai service unavailable"}), 502


# ================= T18 问答页 =================
@ai.get("/ai")
def ai_chat_page():
    """渲染 AI 问答页（沿用主站布局）"""
    # 如果主站要求登录才能用 AI，可加：
    if session.get("is_login") != "true":
        return redirect("/login")
    return render_template("ai_chat.html")