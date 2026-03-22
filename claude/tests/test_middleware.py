import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from auth.middleware import UserContextMiddleware


@pytest.mark.asyncio
async def test_middleware_sets_user_none_when_no_session():
    app = AsyncMock()
    middleware = UserContextMiddleware(app)
    scope = {"type": "http", "session": {}}
    receive = AsyncMock()
    send = AsyncMock()
    await middleware(scope, receive, send)
    app.assert_called_once()
    assert scope.get("state", {}).get("user") is None


@pytest.mark.asyncio
async def test_middleware_skips_non_http():
    app = AsyncMock()
    middleware = UserContextMiddleware(app)
    scope = {"type": "websocket"}
    receive = AsyncMock()
    send = AsyncMock()
    await middleware(scope, receive, send)
    app.assert_called_once()
    assert "state" not in scope


@pytest.mark.asyncio
async def test_middleware_sets_user_from_session():
    app = AsyncMock()
    middleware = UserContextMiddleware(app)
    scope = {"type": "http", "session": {"user_id": 1}}
    receive = AsyncMock()
    send = AsyncMock()

    with patch("auth.middleware.SessionLocal") as mock_session_cls:
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_user

        await middleware(scope, receive, send)
        assert scope["state"]["user"] == mock_user
        mock_db.close.assert_called_once()
