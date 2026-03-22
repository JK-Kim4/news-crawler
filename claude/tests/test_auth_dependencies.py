import pytest
from unittest.mock import MagicMock
from auth.dependencies import get_current_user, require_login, require_admin, LoginRequired
from db.models import User


def _make_request(session=None, hx=False):
    req = MagicMock()
    req.session = session or {}
    if hx:
        req.headers = MagicMock()
        req.headers.get = lambda k, d=None: "true" if k.lower() == "hx-request" else d
    else:
        req.headers = MagicMock()
        req.headers.get = lambda k, d=None: d
    return req


def test_get_current_user_no_session(db):
    req = _make_request()
    user = get_current_user(req, db)
    assert user is None


def test_get_current_user_with_session(db):
    u = User(email="a@b.com", password_hash="h", nickname="n")
    db.add(u)
    db.commit()
    req = _make_request(session={"user_id": u.id})
    user = get_current_user(req, db)
    assert user is not None
    assert user.id == u.id


def test_require_login_raises_for_full_page():
    req = _make_request()
    db = MagicMock()
    with pytest.raises(LoginRequired):
        require_login(req, db)


def test_require_login_htmx_returns_401_with_redirect():
    from fastapi import HTTPException
    req = _make_request(hx=True)
    db = MagicMock()
    with pytest.raises(HTTPException) as exc_info:
        require_login(req, db)
    assert exc_info.value.status_code == 401


def test_require_admin_non_admin(db):
    from fastapi import HTTPException
    u = User(email="a@b.com", password_hash="h", nickname="n", role="user")
    db.add(u)
    db.commit()
    req = _make_request(session={"user_id": u.id})
    with pytest.raises(HTTPException) as exc_info:
        require_admin(req, db)
    assert exc_info.value.status_code == 403


def test_require_admin_passes_for_admin(db):
    u = User(email="admin@b.com", password_hash="h", nickname="admin", role="admin")
    db.add(u)
    db.commit()
    req = _make_request(session={"user_id": u.id})
    result = require_admin(req, db)
    assert result.role == "admin"
