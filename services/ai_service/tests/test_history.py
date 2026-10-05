import pytest
from unittest.mock import AsyncMock, patch

from ai_app.services import history


@pytest.mark.asyncio
async def test_history_append_fail_open():
    """Redis 挂了不抛异常"""
    with patch("ai_app.services.history._client", side_effect=Exception("redis down")):
        # 不应抛
        await history.append("sid", "user", "hello")


@pytest.mark.asyncio
async def test_history_get_fail_open():
    with patch("ai_app.services.history._client", side_effect=Exception("redis down")):
        result = await history.get("sid")
        assert result == []