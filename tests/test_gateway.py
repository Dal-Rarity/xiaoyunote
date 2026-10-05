"""
Flask 网关测试：未登录 401 / 参数校验

在 xiaoyunote 根目录运行（用 flask_project 环境）：
    cd D:/Python/xiaoyunote
    D:/python_env/flask_project/Scripts/python3.exe -m pytest tests/test_gateway.py -q
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

import pytest
from app.app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_unauthenticated_401(client):
    resp = client.post(
        "/api/ai/chat/stream",
        json={"question": "test", "session_id": "sess-abc12345"},
    )
    assert resp.status_code == 401


def test_invalid_question_422(client):
    with client.session_transaction() as sess:
        sess["is_login"] = "true"
        sess["user_id"] = 1
    resp = client.post(
        "/api/ai/chat/stream",
        json={"question": "", "session_id": "sess-abc12345"},
    )
    assert resp.status_code == 422


def test_invalid_session_id_422(client):
    with client.session_transaction() as sess:
        sess["is_login"] = "true"
        sess["user_id"] = 1
    resp = client.post(
        "/api/ai/chat/stream",
        json={"question": "test", "session_id": "short"},
    )
    assert resp.status_code == 422