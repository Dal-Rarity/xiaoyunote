import json
import pytest
from fastapi.testclient import TestClient

from ai_app.config import get_settings
from ai_app.main import app


@pytest.fixture
def client(monkeypatch):
    """测试时关闭内部 Token 校验"""
    s = get_settings()
    monkeypatch.setattr(s, "INTERNAL_TOKEN", "")
    return TestClient(app)


def parse_sse(raw: str):
    """把 SSE 文本解析成 [(event, data_dict)]"""
    events = []
    for block in raw.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        if block.startswith("data: [DONE]"):
            events.append(("[DONE]", None))
            continue
        event = "message"
        data = None
        for line in block.split("\n"):
            if line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:"):
                try:
                    data = json.loads(line[5:].strip())
                except json.JSONDecodeError:
                    data = line[5:].strip()
        events.append((event, data))
    return events


def test_normal_stream_order(client, monkeypatch):
    """正常流：sources → delta* → done → [DONE]"""

    async def fake_stream(q, user_id, session_id=None, history=None,
                          data_type=None, category=None):
        yield {"type": "sources",
               "items": [{"article_id": 75, "title": "三体", "score": 0.85}]}
        yield {"type": "delta", "text": "你好"}
        yield {"type": "delta", "text": "世界"}

    monkeypatch.setattr("ai_app.routers.chat.stream_answer", fake_stream)

    resp = client.post(
        "/api/ai/chat/stream",
        json={"question": "三体", "session_id": "sess-abc12345"},
        headers={"X-User-Id": "1"},
    )
    assert resp.status_code == 200
    events = parse_sse(resp.text)
    types = [e for e, _ in events]
    assert types[0] == "sources"
    assert "delta" in types
    assert "done" in types
    assert types[-1] == "[DONE]"

    sources = next(d for e, d in events if e == "sources")
    assert sources["items"][0]["article_id"] == 75


def test_refused_stream(client, monkeypatch):
    """拒答流：refused → done → [DONE]，无 delta"""

    async def fake_stream(q, user_id, session_id=None, history=None,
                          data_type=None, category=None):
        yield {"type": "refused", "text": "这个问题在我的笔记里没有找到相关内容"}

    monkeypatch.setattr("ai_app.routers.chat.stream_answer", fake_stream)

    resp = client.post(
        "/api/ai/chat/stream",
        json={"question": "天气", "session_id": "sess-abc12345"},
        headers={"X-User-Id": "1"},
    )
    events = parse_sse(resp.text)
    types = [e for e, _ in events]
    assert "refused" in types
    assert "delta" not in types
    assert types[-1] == "[DONE]"


def test_error_to_error_frame(client, monkeypatch):
    """任意异常 → error 帧"""

    async def fake_stream(q, user_id, session_id=None, history=None,
                          data_type=None, category=None):
        yield {"type": "delta", "text": "part"}
        raise RuntimeError("boom")

    monkeypatch.setattr("ai_app.routers.chat.stream_answer", fake_stream)

    resp = client.post(
        "/api/ai/chat/stream",
        json={"question": "test", "session_id": "sess-abc12345"},
        headers={"X-User-Id": "1"},
    )
    events = parse_sse(resp.text)
    types = [e for e, _ in events]
    assert "error" in types
    assert types[-1] == "[DONE]"


def test_invalid_request_422(client):
    """question 为空 → 422"""
    resp = client.post(
        "/api/ai/chat/stream",
        json={"question": "", "session_id": "sess-abc12345"},
        headers={"X-User-Id": "1"},
    )
    assert resp.status_code == 422


def test_invalid_session_id_422(client):
    """session_id 过短 → 422"""
    resp = client.post(
        "/api/ai/chat/stream",
        json={"question": "test", "session_id": "short"},
        headers={"X-User-Id": "1"},
    )
    assert resp.status_code == 422