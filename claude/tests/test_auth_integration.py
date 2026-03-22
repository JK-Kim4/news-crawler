import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from db.models import Base, User
from db.session import get_db
from auth.router import router as auth_router
from auth.dependencies import LoginRequired
from auth.password import hash_password


@pytest.fixture
def app_client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test-secret")

    @app.exception_handler(LoginRequired)
    async def login_required_handler(request, exc):
        return RedirectResponse(url="/auth/login", status_code=303)

    app.include_router(auth_router)
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client, TestSession


@patch("auth.router._get_mail_sender")
def test_full_auth_flow(mock_get_sender, app_client):
    """Register -> verify -> login -> logout full flow."""
    mock_sender = MagicMock()
    mock_get_sender.return_value = mock_sender
    client, Session = app_client

    # 1. Register
    resp = client.post("/auth/register", data={
        "email": "flow@test.com",
        "nickname": "flowuser",
        "password": "TestPass1!",
        "password_confirm": "TestPass1!",
    })
    assert resp.status_code == 200
    mock_sender.send.assert_called_once()

    # 2. Get token from DB
    db = Session()
    user = db.query(User).filter_by(email="flow@test.com").first()
    assert user is not None
    assert user.is_verified is False
    token = user.verify_token
    db.close()

    # 3. Verify email
    resp = client.get(f"/auth/verify?token={token}", follow_redirects=False)
    assert resp.status_code == 303

    # Confirm verified
    db = Session()
    user = db.query(User).filter_by(email="flow@test.com").first()
    assert user.is_verified is True
    db.close()

    # 4. Login
    resp = client.post("/auth/login", data={
        "email": "flow@test.com",
        "password": "TestPass1!",
    }, follow_redirects=False)
    assert resp.status_code == 303

    # 5. Logout
    resp = client.post("/auth/logout", follow_redirects=False)
    assert resp.status_code == 303


@patch("auth.router._get_mail_sender")
def test_password_reset_flow(mock_get_sender, app_client):
    """Forgot password -> reset password flow."""
    mock_sender = MagicMock()
    mock_get_sender.return_value = mock_sender
    client, Session = app_client

    # Create verified user
    db = Session()
    user = User(
        email="reset@test.com",
        password_hash=hash_password("oldpass"),
        nickname="resetter",
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.close()

    # Request reset
    resp = client.post("/auth/forgot-password", data={"email": "reset@test.com"})
    assert resp.status_code == 200
    mock_sender.send.assert_called_once()

    # Get reset token
    db = Session()
    user = db.query(User).filter_by(email="reset@test.com").first()
    token = user.reset_token
    assert token is not None
    db.close()

    # Reset password
    resp = client.post("/auth/reset-password", data={
        "token": token,
        "password": "newpass123",
        "password_confirm": "newpass123",
    }, follow_redirects=False)
    assert resp.status_code == 303

    # Login with new password
    resp = client.post("/auth/login", data={
        "email": "reset@test.com",
        "password": "newpass123",
    }, follow_redirects=False)
    assert resp.status_code == 303


def test_duplicate_registration(app_client):
    """Register with already-verified email shows error."""
    client, Session = app_client
    db = Session()
    user = User(
        email="existing@test.com",
        password_hash=hash_password("pass"),
        nickname="existing",
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.close()

    with patch("auth.router._get_mail_sender"):
        resp = client.post("/auth/register", data={
            "email": "existing@test.com",
            "nickname": "new",
            "password": "password123",
            "password_confirm": "password123",
        })
    assert resp.status_code == 200
    assert "이미 가입된" in resp.text
