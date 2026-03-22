import pytest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware
from db.models import Base, User
from db.session import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from auth.router import router as auth_router
from auth.password import hash_password
from datetime import datetime, timedelta, timezone


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
    app.include_router(auth_router)
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client, TestSession


def test_register_page(app_client):
    client, _ = app_client
    resp = client.get("/auth/register")
    assert resp.status_code == 200


@patch("auth.router._get_mail_sender")
def test_register_creates_user(mock_get_sender, app_client):
    mock_sender = MagicMock()
    mock_get_sender.return_value = mock_sender
    client, Session = app_client
    resp = client.post("/auth/register", data={
        "email": "new@test.com",
        "nickname": "newuser",
        "password": "Password1!",
        "password_confirm": "Password1!",
    })
    assert resp.status_code == 200
    db = Session()
    user = db.query(User).filter_by(email="new@test.com").first()
    assert user is not None
    assert user.is_verified is False
    assert user.verify_token is not None
    mock_sender.send.assert_called_once()
    db.close()


@patch("auth.router._get_mail_sender")
def test_register_duplicate_verified_email(mock_get_sender, app_client):
    mock_sender = MagicMock()
    mock_get_sender.return_value = mock_sender
    client, Session = app_client
    db = Session()
    user = User(
        email="dup@test.com",
        password_hash=hash_password("pass123"),
        nickname="dupuser",
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.close()

    resp = client.post("/auth/register", data={
        "email": "dup@test.com",
        "nickname": "another",
        "password": "Password1!",
        "password_confirm": "Password1!",
    })
    assert resp.status_code == 200
    assert "이미 가입된 이메일입니다" in resp.text


@patch("auth.router._get_mail_sender")
def test_register_duplicate_unverified_resends_email(mock_get_sender, app_client):
    mock_sender = MagicMock()
    mock_get_sender.return_value = mock_sender
    client, Session = app_client
    db = Session()
    user = User(
        email="unv@test.com",
        password_hash=hash_password("OldPass1!"),
        nickname="unvuser",
        is_verified=False,
        verify_token="old-token",
    )
    db.add(user)
    db.commit()
    db.close()

    resp = client.post("/auth/register", data={
        "email": "unv@test.com",
        "nickname": "unvuser",
        "password": "NewPass1!",
        "password_confirm": "NewPass1!",
    })
    assert resp.status_code == 200
    mock_sender.send.assert_called_once()
    db2 = Session()
    updated = db2.query(User).filter_by(email="unv@test.com").first()
    assert updated.verify_token != "old-token"
    db2.close()


def test_register_short_password(app_client):
    client, _ = app_client
    resp = client.post("/auth/register", data={
        "email": "short@test.com",
        "nickname": "shortuser",
        "password": "abc",
        "password_confirm": "abc",
    })
    assert resp.status_code == 200
    assert "8" in resp.text  # error mentions 8 chars


def test_register_password_mismatch(app_client):
    client, _ = app_client
    resp = client.post("/auth/register", data={
        "email": "mismatch@test.com",
        "nickname": "mmuser",
        "password": "Password1!",
        "password_confirm": "Different1!",
    })
    assert resp.status_code == 200
    assert "일치" in resp.text


def test_login_page(app_client):
    client, _ = app_client
    resp = client.get("/auth/login")
    assert resp.status_code == 200


def test_login_success(app_client):
    client, Session = app_client
    db = Session()
    user = User(
        email="login@test.com",
        password_hash=hash_password("pass123"),
        nickname="tester",
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.close()
    resp = client.post("/auth/login", data={
        "email": "login@test.com",
        "password": "pass123",
    }, follow_redirects=False)
    assert resp.status_code == 303


def test_login_unverified(app_client):
    client, Session = app_client
    db = Session()
    user = User(
        email="unverified@test.com",
        password_hash=hash_password("pass123"),
        nickname="tester",
        is_verified=False,
    )
    db.add(user)
    db.commit()
    db.close()
    resp = client.post("/auth/login", data={
        "email": "unverified@test.com",
        "password": "pass123",
    })
    assert resp.status_code == 200
    assert "인증" in resp.text


def test_login_wrong_password(app_client):
    client, Session = app_client
    db = Session()
    user = User(
        email="wrongpw@test.com",
        password_hash=hash_password("correct123"),
        nickname="wpuser",
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.close()
    resp = client.post("/auth/login", data={
        "email": "wrongpw@test.com",
        "password": "wrongpass",
    })
    assert resp.status_code == 200
    assert "잘못된" in resp.text or "이메일" in resp.text or "비밀번호" in resp.text


def test_verify_email(app_client):
    client, Session = app_client
    db = Session()
    user = User(
        email="v@test.com",
        password_hash="h",
        nickname="v",
        verify_token="test-token",
        verify_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(user)
    db.commit()
    db.close()
    resp = client.get("/auth/verify?token=test-token", follow_redirects=False)
    assert resp.status_code == 303
    db2 = Session()
    user = db2.query(User).filter_by(email="v@test.com").first()
    assert user.is_verified is True
    assert user.verify_token is None
    db2.close()


def test_verify_email_expired(app_client):
    client, Session = app_client
    db = Session()
    user = User(
        email="exp@test.com",
        password_hash="h",
        nickname="exp",
        verify_token="expired-token",
        verify_token_expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db.add(user)
    db.commit()
    db.close()
    resp = client.get("/auth/verify?token=expired-token")
    assert resp.status_code == 200
    assert "만료" in resp.text or "expired" in resp.text.lower()


def test_verify_email_invalid_token(app_client):
    client, _ = app_client
    resp = client.get("/auth/verify?token=nonexistent-token")
    assert resp.status_code == 200
    assert "유효하지 않" in resp.text or "invalid" in resp.text.lower()


def test_logout(app_client):
    client, Session = app_client
    db = Session()
    user = User(
        email="logout@test.com",
        password_hash=hash_password("pass123"),
        nickname="logoutuser",
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.close()
    # Login first
    client.post("/auth/login", data={
        "email": "logout@test.com",
        "password": "pass123",
    })
    # Then logout
    resp = client.post("/auth/logout", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/"


@patch("auth.router._get_mail_sender")
def test_resend_verification(mock_get_sender, app_client):
    mock_sender = MagicMock()
    mock_get_sender.return_value = mock_sender
    client, Session = app_client
    db = Session()
    user = User(
        email="resend@test.com",
        password_hash=hash_password("pass123"),
        nickname="resenduser",
        is_verified=False,
        verify_token="old-token",
    )
    db.add(user)
    db.commit()
    db.close()
    resp = client.post("/auth/resend-verification", data={"email": "resend@test.com"})
    assert resp.status_code == 200
    mock_sender.send.assert_called_once()
    db2 = Session()
    updated = db2.query(User).filter_by(email="resend@test.com").first()
    assert updated.verify_token != "old-token"
    db2.close()


def test_forgot_password_page(app_client):
    client, _ = app_client
    resp = client.get("/auth/forgot-password")
    assert resp.status_code == 200


@patch("auth.router._get_mail_sender")
def test_forgot_password_sends_email(mock_get_sender, app_client):
    mock_sender = MagicMock()
    mock_get_sender.return_value = mock_sender
    client, Session = app_client
    db = Session()
    user = User(
        email="forgot@test.com",
        password_hash=hash_password("pass123"),
        nickname="forgotuser",
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.close()
    resp = client.post("/auth/forgot-password", data={"email": "forgot@test.com"})
    assert resp.status_code == 200
    mock_sender.send.assert_called_once()
    db2 = Session()
    updated = db2.query(User).filter_by(email="forgot@test.com").first()
    assert updated.reset_token is not None
    db2.close()


@patch("auth.router._get_mail_sender")
def test_forgot_password_nonexistent_email_still_succeeds(mock_get_sender, app_client):
    """Prevent email enumeration — always show success."""
    mock_sender = MagicMock()
    mock_get_sender.return_value = mock_sender
    client, _ = app_client
    resp = client.post("/auth/forgot-password", data={"email": "nobody@test.com"})
    assert resp.status_code == 200
    mock_sender.send.assert_not_called()


def test_reset_password_page(app_client):
    client, Session = app_client
    db = Session()
    user = User(
        email="reset@test.com",
        password_hash=hash_password("oldpass"),
        nickname="resetuser",
        reset_token="valid-reset-token",
        reset_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(user)
    db.commit()
    db.close()
    resp = client.get("/auth/reset-password?token=valid-reset-token")
    assert resp.status_code == 200


def test_reset_password_page_invalid_token(app_client):
    client, _ = app_client
    resp = client.get("/auth/reset-password?token=bad-token")
    assert resp.status_code == 200
    assert "유효하지 않" in resp.text or "invalid" in resp.text.lower()


def test_reset_password_post_success(app_client):
    client, Session = app_client
    db = Session()
    user = User(
        email="resetpost@test.com",
        password_hash=hash_password("oldpass"),
        nickname="resetpostuser",
        reset_token="reset-token-ok",
        reset_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(user)
    db.commit()
    db.close()
    resp = client.post("/auth/reset-password", data={
        "token": "reset-token-ok",
        "password": "NewPassword1!",
        "password_confirm": "NewPassword1!",
    }, follow_redirects=False)
    assert resp.status_code == 303
    db2 = Session()
    updated = db2.query(User).filter_by(email="resetpost@test.com").first()
    assert updated.reset_token is None
    from auth.password import verify_password
    assert verify_password("NewPassword1!", updated.password_hash)
    db2.close()


def test_reset_password_post_expired_token(app_client):
    client, Session = app_client
    db = Session()
    user = User(
        email="resetexp@test.com",
        password_hash=hash_password("oldpass"),
        nickname="resetexpuser",
        reset_token="expired-reset-token",
        reset_token_expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db.add(user)
    db.commit()
    db.close()
    resp = client.post("/auth/reset-password", data={
        "token": "expired-reset-token",
        "password": "NewPassword1!",
        "password_confirm": "NewPassword1!",
    })
    assert resp.status_code == 200
    assert "만료" in resp.text or "expired" in resp.text.lower()
