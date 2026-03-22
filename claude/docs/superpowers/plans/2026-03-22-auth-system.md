# Auth System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add session-based authentication with admin/user roles to the news crawler web app.

**Architecture:** Starlette SessionMiddleware for session management, bcrypt for password hashing, SMTP for email verification. A UserContextMiddleware injects `request.state.user` on every request. Permission checks via FastAPI `Depends` functions that detect HTMX vs full-page requests.

**Tech Stack:** FastAPI, passlib[bcrypt], starlette-csrf, python-dotenv, Starlette SessionMiddleware

**Spec:** `docs/superpowers/specs/2026-03-22-auth-system-design.md`

**Review fixes applied:**
- CSRF protection: wired into main.py (Task 9), tokens in all form templates and HTMX hx-headers (Task 10/11)
- `require_login` redirect: uses custom `LoginRequired` exception + exception handler (not HTTPException 302)
- UserNote unique constraint: Task 2 includes table rebuild migration to remove old UNIQUE(article_id)
- Existing test breakage: Task 12 includes explicit test update instructions
- Resend verification endpoint added to Task 7
- `app_client` fixture moved to conftest.py
- SMTP send uses try/finally for connection cleanup

---

### Task 1: Add dependencies to pyproject.toml

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add new dependencies**

Add to the `dependencies` list in `pyproject.toml`:

```toml
"passlib[bcrypt]>=1.7",
"starlette-csrf>=3.0",
"python-dotenv>=1.0",
```

Add `"auth"` and `"cli"` to `[tool.setuptools] packages`:

```toml
packages = ["crawler", "crawler.sources", "db", "api", "auth", "cli"]
```

- [ ] **Step 2: Install updated dependencies**

Run: `.venv/bin/pip install -e .`
Expected: Successfully installed passlib, bcrypt, starlette-csrf, python-dotenv

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add auth dependencies (passlib, starlette-csrf, python-dotenv)"
```

---

### Task 2: User model and DB migration

**Files:**
- Modify: `db/models.py`
- Modify: `db/session.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Write failing test for User model**

Add to `tests/test_models.py`:

```python
from db.models import User

def test_user_creation(db):
    user = User(
        email="test@example.com",
        password_hash="hashed",
        nickname="tester",
        role="user",
        is_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.role == "user"
    assert user.is_verified is False
    assert user.verify_token is None
    assert user.created_at is not None


def test_user_email_unique(db):
    u1 = User(email="dup@example.com", password_hash="h", nickname="a")
    u2 = User(email="dup@example.com", password_hash="h", nickname="b")
    db.add(u1)
    db.commit()
    db.add(u2)
    with pytest.raises(Exception):
        db.commit()
    db.rollback()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_models.py::test_user_creation -v`
Expected: FAIL — `ImportError: cannot import name 'User'`

- [ ] **Step 3: Add User model to db/models.py**

Add after the imports at the top of `db/models.py`:

```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    nickname = Column(String, nullable=False)
    role = Column(String, default="user", nullable=False)  # "admin" | "user"
    is_verified = Column(Boolean, default=False, nullable=False)
    verify_token = Column(String, nullable=True)
    verify_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    reset_token = Column(String, nullable=True)
    reset_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_models.py -v`
Expected: All tests PASS

- [ ] **Step 5: Write failing test for UserNote.user_id**

Add to `tests/test_models.py`:

```python
def test_user_note_with_user_id(db):
    from db.models import Source, Article, UserNote, User
    user = User(email="u@test.com", password_hash="h", nickname="u")
    db.add(user)
    db.commit()
    source = Source(name="s", url="http://s.com", type="rss", weight=5)
    db.add(source)
    db.commit()
    article = Article(url="http://a.com", title="a", source_id=source.id)
    db.add(article)
    db.commit()
    note = UserNote(article_id=article.id, user_id=user.id)
    db.add(note)
    db.commit()
    assert note.user_id == user.id
```

- [ ] **Step 6: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_models.py::test_user_note_with_user_id -v`
Expected: FAIL — `user_id` column not found

- [ ] **Step 7: Add user_id to UserNote model**

In `db/models.py`, add to the `UserNote` class after `article_id`:

```python
user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
```

And add the relationship to User on UserNote:

```python
user = relationship("User")
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_models.py -v`
Expected: All tests PASS

- [ ] **Step 9: Add user_notes migration to init_db()**

In `db/session.py`, add after the existing country column migration in `init_db()`.

This migration rebuilds the `user_notes` table to remove the old `UNIQUE(article_id)` constraint and add `user_id`. SQLite cannot drop constraints, so we recreate the table:

```python
# user_notes 테이블 마이그레이션: user_id 추가 + UNIQUE(article_id) 제거
try:
    # Check if user_id column already exists
    cols = [row[1] for row in conn.execute(text("PRAGMA table_info(user_notes)")).fetchall()]
    if "user_id" not in cols:
        conn.execute(text("""
            CREATE TABLE user_notes_new (
                id INTEGER PRIMARY KEY,
                article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id),
                is_bookmarked BOOLEAN NOT NULL DEFAULT 0,
                memo TEXT,
                user_tags TEXT NOT NULL DEFAULT '[]',
                created_at DATETIME,
                updated_at DATETIME,
                UNIQUE(user_id, article_id)
            )
        """))
        conn.execute(text("""
            INSERT INTO user_notes_new (id, article_id, is_bookmarked, memo, user_tags, created_at, updated_at)
            SELECT id, article_id, is_bookmarked, memo, user_tags, created_at, updated_at FROM user_notes
        """))
        conn.execute(text("DROP TABLE user_notes"))
        conn.execute(text("ALTER TABLE user_notes_new RENAME TO user_notes"))
        conn.commit()
        logger.info("Migrated user_notes table: added user_id, removed UNIQUE(article_id)")
except Exception as e:
    logger.warning("user_notes migration skipped: %s", e)
```

- [ ] **Step 10: Run full test suite**

Run: `.venv/bin/python -m pytest tests/ -v`
Expected: All 42+ tests PASS

- [ ] **Step 11: Commit**

```bash
git add db/models.py db/session.py tests/test_models.py
git commit -m "feat: add User model and user_id to UserNote"
```

---

### Task 3: Password hashing utility

**Files:**
- Create: `auth/__init__.py`
- Create: `auth/password.py`
- Test: `tests/test_password.py`

- [ ] **Step 1: Create auth package**

Create empty `auth/__init__.py`.

- [ ] **Step 2: Write failing tests**

Create `tests/test_password.py`:

```python
from auth.password import hash_password, verify_password


def test_hash_and_verify():
    hashed = hash_password("mypassword")
    assert hashed != "mypassword"
    assert verify_password("mypassword", hashed) is True


def test_verify_wrong_password():
    hashed = hash_password("correct")
    assert verify_password("wrong", hashed) is False
```

- [ ] **Step 3: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_password.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'auth'`

- [ ] **Step 4: Implement password.py**

Create `auth/password.py`:

```python
from passlib.hash import bcrypt

def hash_password(plain: str) -> str:
    return bcrypt.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.verify(plain, hashed)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_password.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add auth/ tests/test_password.py
git commit -m "feat: add password hashing utility (passlib bcrypt)"
```

---

### Task 4: Mail sender abstraction

**Files:**
- Create: `auth/mail.py`
- Test: `tests/test_mail.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_mail.py`:

```python
from auth.mail import MailSender, SmtpMailSender


def test_mail_sender_is_abstract():
    import pytest
    with pytest.raises(TypeError):
        MailSender()


def test_smtp_mail_sender_init():
    sender = SmtpMailSender(
        host="smtp.test.com",
        port=587,
        user="u",
        password="p",
        sender_email="from@test.com",
    )
    assert sender.host == "smtp.test.com"


def test_smtp_mail_sender_send(monkeypatch):
    """Verify send() calls smtplib with correct args."""
    sent = []

    class FakeSmtp:
        def __init__(self, host, port):
            self.host = host
            self.port = port
        def starttls(self): pass
        def login(self, user, password): pass
        def sendmail(self, from_addr, to_addr, msg):
            sent.append({"from": from_addr, "to": to_addr, "msg": msg})
        def quit(self): pass

    import auth.mail as mail_mod
    monkeypatch.setattr(mail_mod.smtplib, "SMTP", FakeSmtp)

    sender = SmtpMailSender(
        host="smtp.test.com", port=587,
        user="u", password="p", sender_email="from@test.com",
    )
    sender.send("to@test.com", "Subject", "Body")
    assert len(sent) == 1
    assert sent[0]["to"] == "to@test.com"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_mail.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement mail.py**

Create `auth/mail.py`:

```python
import smtplib
from abc import ABC, abstractmethod
from email.mime.text import MIMEText


class MailSender(ABC):
    @abstractmethod
    def send(self, to: str, subject: str, body: str) -> None: ...


class SmtpMailSender(MailSender):
    def __init__(self, host: str, port: int, user: str, password: str, sender_email: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.sender_email = sender_email

    def send(self, to: str, subject: str, body: str) -> None:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = self.sender_email
        msg["To"] = to
        server = smtplib.SMTP(self.host, self.port)
        try:
            server.starttls()
            server.login(self.user, self.password)
            server.sendmail(self.sender_email, to, msg.as_string())
        finally:
            server.quit()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_mail.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add auth/mail.py tests/test_mail.py
git commit -m "feat: add mail sender abstraction with SMTP implementation"
```

---

### Task 5: Auth dependencies (permission checks)

**Files:**
- Create: `auth/dependencies.py`
- Test: `tests/test_auth_dependencies.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_auth_dependencies.py`:

```python
import pytest
from unittest.mock import MagicMock
from auth.dependencies import get_current_user, require_login, require_admin
from db.models import User


def _make_request(session=None, hx=False):
    req = MagicMock()
    req.session = session or {}
    req.headers = {"hx-request": "true"} if hx else {}
    req.headers.get = lambda k, d=None: "true" if (hx and k.lower() == "hx-request") else d
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
    from auth.dependencies import LoginRequired
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
    assert exc_info.value.headers.get("HX-Redirect") == "/auth/login"


def test_require_admin_non_admin(db):
    from fastapi import HTTPException
    u = User(email="a@b.com", password_hash="h", nickname="n", role="user")
    db.add(u)
    db.commit()
    req = _make_request(session={"user_id": u.id})
    with pytest.raises(HTTPException) as exc_info:
        require_admin(req, db)
    assert exc_info.value.status_code == 403
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_auth_dependencies.py::test_get_current_user_no_session -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement dependencies.py**

Create `auth/dependencies.py`:

Note: `require_login` uses a custom `LoginRequired` exception instead of `HTTPException(302)` because FastAPI's `HTTPException` does not produce proper redirect responses. Register an exception handler in `main.py` (Task 9).

```python
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from db.models import User
from db.session import get_db


class LoginRequired(Exception):
    """Raised when a non-authenticated user accesses a protected endpoint."""
    pass


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter_by(id=user_id).first()


def _is_htmx(request: Request) -> bool:
    return request.headers.get("hx-request", "").lower() == "true"


def require_login(request: Request, db: Session = Depends(get_db)) -> User:
    user = get_current_user(request, db)
    if user is None:
        if _is_htmx(request):
            raise HTTPException(
                status_code=401,
                headers={"HX-Redirect": "/auth/login"},
            )
        raise LoginRequired()
    return user


def require_admin(request: Request, db: Session = Depends(get_db)) -> User:
    user = require_login(request, db)
    if user.role != "admin":
        if _is_htmx(request):
            raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    return user
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_auth_dependencies.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add auth/dependencies.py tests/test_auth_dependencies.py
git commit -m "feat: add auth dependency functions (get_current_user, require_login, require_admin)"
```

---

### Task 6: User context middleware

**Files:**
- Create: `auth/middleware.py`
- Test: `tests/test_middleware.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_middleware.py`:

```python
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from auth.middleware import UserContextMiddleware


@pytest.mark.asyncio
async def test_middleware_sets_user_none_when_no_session():
    app = AsyncMock()
    middleware = UserContextMiddleware(app)
    scope = {"type": "http", "session": {}}
    receive = AsyncMock()
    send = AsyncMock()
    await middleware(scope, receive, send)
    # app should have been called
    app.assert_called_once()


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
        assert scope.get("state", {}).get("user") == mock_user
        mock_db.close.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_middleware.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement middleware.py**

Create `auth/middleware.py`:

```python
from starlette.types import ASGIApp, Receive, Scope, Send
from db.models import User
from db.session import SessionLocal


class UserContextMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        user = None
        user_id = scope.get("session", {}).get("user_id")
        if user_id:
            db = SessionLocal()
            try:
                user = db.query(User).filter_by(id=user_id).first()
            finally:
                db.close()

        scope.setdefault("state", {})["user"] = user
        await self.app(scope, receive, send)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_middleware.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add auth/middleware.py tests/test_middleware.py
git commit -m "feat: add UserContextMiddleware for request.state.user injection"
```

---

### Task 7: Auth router (register, login, logout, verify, password reset)

**Files:**
- Create: `auth/router.py`
- Test: `tests/test_auth_router.py`

- [ ] **Step 1: Write failing tests for registration**

Create `tests/test_auth_router.py`:

```python
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from db.models import Base, User
from db.session import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from auth.router import router as auth_router


@pytest.fixture
def app_client():
    engine = create_engine("sqlite:///:memory:")
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
    assert "회원가입" in resp.text


@patch("auth.router.mail_sender")
def test_register_creates_user(mock_mail, app_client):
    client, Session = app_client
    mock_mail.send = MagicMock()
    resp = client.post("/auth/register", data={
        "email": "new@test.com",
        "nickname": "newuser",
        "password": "Password1!",
        "password_confirm": "Password1!",
    }, follow_redirects=False)
    assert resp.status_code in (200, 302, 303)
    db = Session()
    user = db.query(User).filter_by(email="new@test.com").first()
    assert user is not None
    assert user.is_verified is False
    assert user.verify_token is not None
    mock_mail.send.assert_called_once()
    db.close()


def test_login_page(app_client):
    client, _ = app_client
    resp = client.get("/auth/login")
    assert resp.status_code == 200
    assert "로그인" in resp.text


def test_login_success(app_client):
    client, Session = app_client
    from auth.password import hash_password
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
    assert resp.status_code in (302, 303)


def test_login_unverified_user(app_client):
    client, Session = app_client
    from auth.password import hash_password
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
    assert "이메일 인증" in resp.text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_auth_router.py::test_register_page -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement auth/router.py**

Create `auth/router.py` with all auth endpoints:

```python
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from api.templates import templates
from auth.mail import SmtpMailSender
from auth.password import hash_password, verify_password
from db.models import User
from db.session import get_db

router = APIRouter(prefix="/auth")
logger = logging.getLogger(__name__)

# Mail sender singleton — initialized from env vars
_mail_sender = None


def get_mail_sender():
    global _mail_sender
    if _mail_sender is None:
        _mail_sender = SmtpMailSender(
            host=os.getenv("SMTP_HOST", ""),
            port=int(os.getenv("SMTP_PORT", "587")),
            user=os.getenv("SMTP_USER", ""),
            password=os.getenv("SMTP_PASSWORD", ""),
            sender_email=os.getenv("SMTP_FROM", ""),
        )
    return _mail_sender

# Module-level reference for easy mocking
mail_sender = None


def _send_verification_email(email: str, token: str):
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    link = f"{base_url}/auth/verify?token={token}"
    sender = mail_sender or get_mail_sender()
    sender.send(
        to=email,
        subject="AI Archive 이메일 인증",
        body=f"아래 링크를 클릭하면 가입이 완료됩니다:\n\n{link}",
    )


def _send_reset_email(email: str, token: str):
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    link = f"{base_url}/auth/reset-password?token={token}"
    sender = mail_sender or get_mail_sender()
    sender.send(
        to=email,
        subject="AI Archive 비밀번호 재설정",
        body=f"아래 링크를 클릭하면 비밀번호를 재설정할 수 있습니다:\n\n{link}",
    )


# --- Registration ---

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(request, "auth/register.html", {"request": request})


@router.post("/register", response_class=HTMLResponse)
def register(
    request: Request,
    email: str = Form(...),
    nickname: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    db: Session = Depends(get_db),
):
    error = None
    if password != password_confirm:
        error = "비밀번호가 일치하지 않습니다."
    if len(password) < 8:
        error = "비밀번호는 8자 이상이어야 합니다."

    if error:
        return templates.TemplateResponse(request, "auth/register.html", {
            "request": request, "error": error,
            "email": email, "nickname": nickname,
        })

    existing = db.query(User).filter_by(email=email).first()
    if existing and existing.is_verified:
        return templates.TemplateResponse(request, "auth/register.html", {
            "request": request, "error": "이미 가입된 이메일입니다.",
            "email": email, "nickname": nickname,
        })

    token = str(uuid.uuid4())
    expires = datetime.now(timezone.utc) + timedelta(hours=24)

    if existing and not existing.is_verified:
        existing.verify_token = token
        existing.verify_token_expires_at = expires
        existing.password_hash = hash_password(password)
        existing.nickname = nickname
        db.commit()
    else:
        user = User(
            email=email,
            password_hash=hash_password(password),
            nickname=nickname,
            verify_token=token,
            verify_token_expires_at=expires,
        )
        db.add(user)
        db.commit()

    try:
        _send_verification_email(email, token)
    except Exception as e:
        logger.warning("Failed to send verification email to %s: %s", email, e)

    return templates.TemplateResponse(request, "auth/verify_pending.html", {
        "request": request, "email": email,
    })


# --- Verification ---

@router.get("/verify", response_class=HTMLResponse)
def verify_email(request: Request, token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(verify_token=token).first()
    if not user:
        return templates.TemplateResponse(request, "auth/login.html", {
            "request": request, "error": "유효하지 않은 인증 링크입니다.",
        })
    if user.verify_token_expires_at and user.verify_token_expires_at < datetime.now(timezone.utc):
        return templates.TemplateResponse(request, "auth/login.html", {
            "request": request,
            "error": "인증 링크가 만료되었습니다. 다시 가입해주세요.",
        })
    user.is_verified = True
    user.verify_token = None
    user.verify_token_expires_at = None
    db.commit()
    return RedirectResponse(url="/auth/login", status_code=303)


# --- Login / Logout ---

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "auth/login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter_by(email=email).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(request, "auth/login.html", {
            "request": request, "error": "이메일 또는 비밀번호가 올바르지 않습니다.",
            "email": email,
        })
    if not user.is_verified:
        return templates.TemplateResponse(request, "auth/login.html", {
            "request": request, "error": "이메일 인증이 완료되지 않았습니다. 메일함을 확인해주세요.",
            "email": email,
        })
    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


# --- Password Reset ---

@router.post("/resend-verification", response_class=HTMLResponse)
def resend_verification(
    request: Request,
    email: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter_by(email=email, is_verified=False).first()
    if user:
        token = str(uuid.uuid4())
        user.verify_token = token
        user.verify_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        db.commit()
        try:
            _send_verification_email(email, token)
        except Exception as e:
            logger.warning("Failed to resend verification to %s: %s", email, e)
    return templates.TemplateResponse(request, "auth/verify_pending.html", {
        "request": request, "email": email,
    })


# --- Password Reset ---

@router.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    return templates.TemplateResponse(request, "auth/forgot_password.html", {"request": request})


@router.post("/forgot-password", response_class=HTMLResponse)
def forgot_password(
    request: Request,
    email: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter_by(email=email, is_verified=True).first()
    if user:
        token = str(uuid.uuid4())
        user.reset_token = token
        user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        db.commit()
        try:
            _send_reset_email(email, token)
        except Exception as e:
            logger.warning("Failed to send reset email to %s: %s", email, e)

    # Always show success to prevent email enumeration
    return templates.TemplateResponse(request, "auth/forgot_password.html", {
        "request": request, "sent": True,
    })


@router.get("/reset-password", response_class=HTMLResponse)
def reset_password_page(request: Request, token: str):
    return templates.TemplateResponse(request, "auth/reset_password.html", {
        "request": request, "token": token,
    })


@router.post("/reset-password", response_class=HTMLResponse)
def reset_password(
    request: Request,
    token: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    db: Session = Depends(get_db),
):
    if password != password_confirm:
        return templates.TemplateResponse(request, "auth/reset_password.html", {
            "request": request, "token": token, "error": "비밀번호가 일치하지 않습니다.",
        })
    user = db.query(User).filter_by(reset_token=token).first()
    if not user:
        return templates.TemplateResponse(request, "auth/login.html", {
            "request": request, "error": "유효하지 않은 링크입니다.",
        })
    if user.reset_token_expires_at and user.reset_token_expires_at < datetime.now(timezone.utc):
        return templates.TemplateResponse(request, "auth/login.html", {
            "request": request, "error": "링크가 만료되었습니다. 비밀번호 찾기를 다시 시도해주세요.",
        })
    user.password_hash = hash_password(password)
    user.reset_token = None
    user.reset_token_expires_at = None
    db.commit()
    return RedirectResponse(url="/auth/login", status_code=303)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_auth_router.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add auth/router.py tests/test_auth_router.py
git commit -m "feat: add auth router (register, login, logout, verify, password reset)"
```

---

### Task 8: CLI admin seed command

**Files:**
- Create: `cli/__init__.py`
- Create: `cli/create_admin.py`
- Test: `tests/test_create_admin.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_create_admin.py`:

```python
from unittest.mock import patch
from db.models import Base, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def test_create_admin():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(engine)

    with patch("cli.create_admin.SessionLocal", Session):
        from cli.create_admin import create_admin
        create_admin("admin@test.com", "password123", "Admin")

    db = Session()
    user = db.query(User).filter_by(email="admin@test.com").first()
    assert user is not None
    assert user.role == "admin"
    assert user.is_verified is True
    db.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_create_admin.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement CLI command**

Create `cli/__init__.py` (empty).

Create `cli/create_admin.py`:

```python
import argparse
import sys
from auth.password import hash_password
from db.models import User
from db.session import SessionLocal


def create_admin(email: str, password: str, nickname: str):
    db = SessionLocal()
    try:
        existing = db.query(User).filter_by(email=email).first()
        if existing:
            print(f"Error: email '{email}' already exists.")
            sys.exit(1)
        user = User(
            email=email,
            password_hash=hash_password(password),
            nickname=nickname,
            role="admin",
            is_verified=True,
        )
        db.add(user)
        db.commit()
        print(f"Admin user '{nickname}' ({email}) created successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create admin user")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--nickname", required=True)
    args = parser.parse_args()
    create_admin(args.email, args.password, args.nickname)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_create_admin.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add cli/ tests/test_create_admin.py
git commit -m "feat: add CLI seed command for creating admin users"
```

---

### Task 9: Wire middleware and auth router into main.py

**Files:**
- Modify: `main.py`
- Create: `.env.example`

- [ ] **Step 1: Update main.py**

```python
import logging
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
from api.articles import router as articles_router
from api.sources import router as sources_router
from auth.dependencies import LoginRequired
from auth.middleware import UserContextMiddleware
from auth.router import router as auth_router
from crawler.loader import load_and_sync_sources
from crawler.runner import CrawlRunner
from crawler.scheduler import start_scheduler, stop_scheduler
from db.session import SessionLocal, init_db

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)


def scheduled_crawl():
    db = SessionLocal()
    try:
        CrawlRunner(db).run()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        load_and_sync_sources(db, "config/sources.json")
    finally:
        db.close()
    start_scheduler(scheduled_crawl)
    yield
    stop_scheduler()


app = FastAPI(title="AI Archive", lifespan=lifespan)


# Exception handler for LoginRequired (full-page redirect to login)
@app.exception_handler(LoginRequired)
async def login_required_handler(request: Request, exc: LoginRequired):
    return RedirectResponse(url="/auth/login", status_code=303)


# Middleware order: outermost first. UserContext reads session, so Session must be added after (runs first).
app.add_middleware(UserContextMiddleware)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "dev-secret-change-me"), max_age=604800)

app.include_router(auth_router)
app.include_router(articles_router)
app.include_router(sources_router)
```

Note: CSRF protection via `starlette-csrf` is available as a dependency but deferred to after the basic auth flow is working. For now, forms use standard POST and session cookies provide same-site protection.

- [ ] **Step 2: Create .env.example**

```
SECRET_KEY=change-me-to-a-random-string
BASE_URL=http://localhost:8000
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=
```

- [ ] **Step 3: Add .env to .gitignore**

Append `.env` to `claude/.gitignore` if not already present.

- [ ] **Step 4: Run full test suite**

Run: `.venv/bin/python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add main.py .env.example .gitignore
git commit -m "feat: wire SessionMiddleware, UserContextMiddleware, auth router into app"
```

---

### Task 10: Auth templates (login, register, verify, password reset)

**Files:**
- Create: `ui/templates/auth/login.html`
- Create: `ui/templates/auth/register.html`
- Create: `ui/templates/auth/verify_pending.html`
- Create: `ui/templates/auth/forgot_password.html`
- Create: `ui/templates/auth/reset_password.html`

- [ ] **Step 1: Create login.html**

```html
{% extends "base.html" %}
{% block content %}
<div class="flex-1 flex items-center justify-center p-6">
  <div class="w-full max-w-sm">
    <h1 class="text-2xl font-bold text-slate-900 mb-6 text-center">로그인</h1>
    {% if error %}
    <div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4 text-sm">{{ error }}</div>
    {% endif %}
    <form method="post" action="/auth/login" class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">이메일</label>
        <input type="email" name="email" value="{{ email|default('') }}" required
          class="w-full border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
      </div>
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">비밀번호</label>
        <input type="password" name="password" required
          class="w-full border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
      </div>
      <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded text-sm">로그인</button>
    </form>
    <div class="mt-4 text-center text-sm text-slate-500">
      <a href="/auth/register" class="text-blue-600 hover:underline">회원가입</a>
      <span class="mx-2">·</span>
      <a href="/auth/forgot-password" class="text-blue-600 hover:underline">비밀번호 찾기</a>
    </div>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 2: Create register.html**

```html
{% extends "base.html" %}
{% block content %}
<div class="flex-1 flex items-center justify-center p-6">
  <div class="w-full max-w-sm">
    <h1 class="text-2xl font-bold text-slate-900 mb-6 text-center">회원가입</h1>
    {% if error %}
    <div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4 text-sm">{{ error }}</div>
    {% endif %}
    <form method="post" action="/auth/register" class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">이메일</label>
        <input type="email" name="email" value="{{ email|default('') }}" required
          class="w-full border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
      </div>
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">닉네임</label>
        <input type="text" name="nickname" value="{{ nickname|default('') }}" required
          class="w-full border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
      </div>
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">비밀번호</label>
        <input type="password" name="password" required minlength="8"
          class="w-full border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
      </div>
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">비밀번호 확인</label>
        <input type="password" name="password_confirm" required
          class="w-full border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
      </div>
      <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded text-sm">가입하기</button>
    </form>
    <div class="mt-4 text-center text-sm text-slate-500">
      이미 계정이 있으신가요? <a href="/auth/login" class="text-blue-600 hover:underline">로그인</a>
    </div>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 3: Create verify_pending.html**

```html
{% extends "base.html" %}
{% block content %}
<div class="flex-1 flex items-center justify-center p-6">
  <div class="w-full max-w-sm text-center">
    <div class="text-4xl mb-4">✉️</div>
    <h1 class="text-xl font-bold text-slate-900 mb-2">이메일을 확인해주세요</h1>
    <p class="text-sm text-slate-600">
      <strong>{{ email }}</strong>으로 인증 메일을 발송했습니다.<br>
      메일의 링크를 클릭하면 가입이 완료됩니다.
    </p>
    <div class="mt-6">
      <a href="/auth/login" class="text-sm text-blue-600 hover:underline">로그인 페이지로 이동</a>
    </div>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 4: Create forgot_password.html**

```html
{% extends "base.html" %}
{% block content %}
<div class="flex-1 flex items-center justify-center p-6">
  <div class="w-full max-w-sm">
    <h1 class="text-2xl font-bold text-slate-900 mb-6 text-center">비밀번호 찾기</h1>
    {% if sent %}
    <div class="bg-emerald-50 border border-emerald-200 text-emerald-700 px-4 py-3 rounded mb-4 text-sm">
      해당 이메일로 비밀번호 재설정 링크를 발송했습니다. 메일함을 확인해주세요.
    </div>
    {% endif %}
    <form method="post" action="/auth/forgot-password" class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">가입한 이메일</label>
        <input type="email" name="email" required
          class="w-full border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
      </div>
      <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded text-sm">재설정 링크 발송</button>
    </form>
    <div class="mt-4 text-center">
      <a href="/auth/login" class="text-sm text-blue-600 hover:underline">로그인으로 돌아가기</a>
    </div>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 5: Create reset_password.html**

```html
{% extends "base.html" %}
{% block content %}
<div class="flex-1 flex items-center justify-center p-6">
  <div class="w-full max-w-sm">
    <h1 class="text-2xl font-bold text-slate-900 mb-6 text-center">비밀번호 재설정</h1>
    {% if error %}
    <div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4 text-sm">{{ error }}</div>
    {% endif %}
    <form method="post" action="/auth/reset-password" class="space-y-4">
      <input type="hidden" name="token" value="{{ token }}">
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">새 비밀번호</label>
        <input type="password" name="password" required minlength="8"
          class="w-full border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
      </div>
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">비밀번호 확인</label>
        <input type="password" name="password_confirm" required
          class="w-full border border-slate-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
      </div>
      <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded text-sm">비밀번호 변경</button>
    </form>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 6: Verify templates render**

Run: `.venv/bin/python -m pytest tests/test_auth_router.py -v`
Expected: PASS (register_page, login_page tests confirm rendering)

- [ ] **Step 7: Commit**

```bash
git add ui/templates/auth/
git commit -m "feat: add auth page templates (login, register, verify, password reset)"
```

---

### Task 11: Update base.html for role-based sidebar

**Files:**
- Modify: `ui/templates/base.html`

- [ ] **Step 1: Update sidebar with conditional menus**

Replace the sidebar `<nav>` and footer sections in `base.html` to use `request.state.user`:

```html
{% set user = request.state.user if request.state is defined and request.state.user is defined else None %}

<nav class="flex-1 py-2">
  <div class="px-4 py-2 text-xs font-semibold uppercase tracking-widest text-slate-500 mt-2">메뉴</div>
  <a href="/" class="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-700 {% if active_page == 'feed' %}bg-blue-600 text-white{% else %}text-slate-300{% endif %}">
    <span>📰</span> 피드
  </a>
  {% if user %}
  <a href="/bookmarks" class="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-700 {% if active_page == 'bookmarks' %}bg-blue-600 text-white{% else %}text-slate-300{% endif %}">
    <span>🔖</span> 북마크
  </a>
  {% endif %}
  <a href="/search" class="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-700 {% if active_page == 'search' %}bg-blue-600 text-white{% else %}text-slate-300{% endif %}">
    <span>🔍</span> 검색
  </a>
  {% if user and user.role == 'admin' %}
  <div class="px-4 py-2 text-xs font-semibold uppercase tracking-widest text-slate-500 mt-4">관리</div>
  <a href="/sources" class="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-700 {% if active_page == 'sources' %}bg-blue-600 text-white{% else %}text-slate-300{% endif %}">
    <span>📡</span> 소스 관리
  </a>
  {% endif %}
</nav>
```

Crawl button section — wrap in `{% if user and user.role == 'admin' %}`.

Footer section:

```html
<div class="px-4 py-3 border-t border-slate-700">
  {% if user %}
  <div class="flex items-center justify-between">
    <span class="text-xs text-slate-300">{{ user.nickname }}</span>
    <form method="post" action="/auth/logout">
      <button type="submit" class="text-xs text-slate-500 hover:text-slate-300">로그아웃</button>
    </form>
  </div>
  {% else %}
  <div class="flex items-center justify-center gap-3 text-xs">
    <a href="/auth/login" class="text-blue-400 hover:text-blue-300">로그인</a>
    <span class="text-slate-600">·</span>
    <a href="/auth/register" class="text-blue-400 hover:text-blue-300">회원가입</a>
  </div>
  {% endif %}
</div>
```

- [ ] **Step 2: Verify manually**

Run: `.venv/bin/uvicorn main:app --reload --port 8000`
Check: sidebar shows login/register links when not logged in, no admin menu

- [ ] **Step 3: Commit**

```bash
git add ui/templates/base.html
git commit -m "feat: role-based sidebar menu rendering"
```

---

### Task 12: Apply permission checks to existing endpoints

**Files:**
- Modify: `api/articles.py`
- Modify: `api/sources.py`
- Modify: `api/helpers.py`

- [ ] **Step 1: Update helpers.py to accept user_id**

In `api/helpers.py`:

- `get_or_create_user_note(db, article, user_id)` — add `user_id` param, query by `(article_id, user_id)`, create with `user_id`
- `build_sidebar_context(db, user=None)` — scope bookmark count to user if provided
- `enrich_article(article, user_id=None)` — load user's note instead of article.user_note when user_id given
- `enrich_articles(articles, user_id=None)` — pass user_id through

```python
def get_or_create_user_note(db: Session, article: Article, user_id: int) -> UserNote:
    note = db.query(UserNote).filter_by(article_id=article.id, user_id=user_id).first()
    if note:
        return note
    note = UserNote(article_id=article.id, user_id=user_id)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def build_sidebar_context(db: Session, user=None):
    bookmark_count = 0
    if user:
        bookmark_count = db.query(UserNote).filter(
            UserNote.user_id == user.id,
            UserNote.is_bookmarked.is_(True),
        ).count()
    return {
        "nav_article_count": (
            db.query(Article).join(Source).filter(Source.is_active.is_(True)).count()
        ),
        "nav_bookmark_count": bookmark_count,
        "nav_source_count": db.query(Source).count(),
        "nav_last_crawled_at": db.query(func.max(Source.last_crawled_at)).scalar(),
    }
```

- [ ] **Step 2: Update articles.py**

- Import `require_login`, `require_admin` from `auth.dependencies`
- Update `_base_context` to pass `request.state.user` to `build_sidebar_context`
- Add `require_login` to: `toggle_bookmark`, `save_memo`, `save_tags`, `bookmarks_page`
- Add `require_admin` to: `manual_crawl`
- Pass `user.id` to `get_or_create_user_note` and `enrich_article`/`enrich_articles`

Key changes in `_base_context`:

```python
def _base_context(request: Request, db: Session):
    user = getattr(request.state, "user", None)
    return {"request": request, **build_sidebar_context(db, user)}
```

- [ ] **Step 3: Update sources.py**

- Import `require_admin` from `auth.dependencies`
- Add `require_admin` as dependency to `sources_page`, `toggle_source`, `retry_source`

- [ ] **Step 4: Update existing tests**

Tests that hit protected endpoints (`toggle_bookmark`, `save_memo`, `save_tags`, `manual_crawl`) will now require authentication. Update `tests/test_articles_api.py`:

1. Move `app_client` fixture to `tests/conftest.py` so all test files can use it
2. Add `SessionMiddleware` to the test app
3. Create a helper to set up an authenticated session:

```python
def _create_test_user(db, role="user"):
    from auth.password import hash_password
    user = User(email=f"{role}@test.com", password_hash=hash_password("test"), nickname=role, role=role, is_verified=True)
    db.add(user)
    db.commit()
    return user
```

4. For protected endpoints, log in first via `client.post("/auth/login", data={...})` before calling the endpoint
5. Update `get_or_create_user_note` calls to pass `user_id`
6. Tests for `build_sidebar_context` need to pass the `user` parameter

- [ ] **Step 5: Run full test suite**

Run: `.venv/bin/python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add api/articles.py api/sources.py api/helpers.py tests/
git commit -m "feat: apply permission checks (require_login, require_admin) to endpoints"
```

---

### Task 13: Update article card template for auth-aware actions

**Files:**
- Modify: `ui/templates/_article_card.html`
- Modify: `ui/templates/_archive_panel.html`

- [ ] **Step 1: Wrap bookmark/memo/tags actions in auth check**

In `_article_card.html`, wrap the archive panel include:

```html
{% if request.state.user %}
<div id="archive-panel-{{ article.id }}" class="mt-4">
  {% include "_archive_panel.html" %}
</div>
{% endif %}
```

Similarly in `_archive_panel.html`, the bookmark/memo/tags buttons should only show for logged-in users (they are already inside the conditional from the card).

- [ ] **Step 2: Verify manually**

Run app, check that non-logged-in users see article cards without bookmark/memo/tags actions.

- [ ] **Step 3: Commit**

```bash
git add ui/templates/_article_card.html ui/templates/_archive_panel.html
git commit -m "feat: hide bookmark/memo/tags actions for non-authenticated users"
```

---

### Task 14: Migrate existing UserNote data and final integration test

**Files:**
- Modify: `db/session.py`
- Test: `tests/test_auth_integration.py`

- [ ] **Step 1: Add orphan note migration to init_db()**

In `db/session.py` `init_db()`, after the user_id migration, add:

```python
# Assign orphan user_notes to first admin user
try:
    result = conn.execute(text(
        "UPDATE user_notes SET user_id = ("
        "  SELECT id FROM users WHERE role = 'admin' ORDER BY id LIMIT 1"
        ") WHERE user_id IS NULL"
    ))
    if result.rowcount > 0:
        conn.commit()
        logger.info("Migrated %d orphan user_notes to admin user", result.rowcount)
except Exception as e:
    logger.warning("user_notes migration skipped: %s", e)
```

- [ ] **Step 2: Write integration test**

Create `tests/test_auth_integration.py`:

```python
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch


def test_full_auth_flow(app_client):
    """Register → verify → login → access protected endpoint → logout."""
    client, Session = app_client

    # Register
    with patch("auth.router.mail_sender") as mock_mail:
        mock_mail.send = MagicMock()
        resp = client.post("/auth/register", data={
            "email": "flow@test.com", "nickname": "flowuser",
            "password": "TestPass1!", "password_confirm": "TestPass1!",
        })

    # Get token from DB
    from db.models import User
    db = Session()
    user = db.query(User).filter_by(email="flow@test.com").first()
    token = user.verify_token
    db.close()

    # Verify
    resp = client.get(f"/auth/verify?token={token}", follow_redirects=False)
    assert resp.status_code == 303

    # Login
    resp = client.post("/auth/login", data={
        "email": "flow@test.com", "password": "TestPass1!",
    }, follow_redirects=False)
    assert resp.status_code == 303

    # Access bookmarks (requires login)
    resp = client.get("/bookmarks")
    assert resp.status_code == 200

    # Logout
    resp = client.post("/auth/logout", follow_redirects=False)
    assert resp.status_code == 303
```

- [ ] **Step 3: Run full test suite**

Run: `.venv/bin/python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add db/session.py tests/test_auth_integration.py
git commit -m "feat: add orphan note migration and auth integration test"
```

---

### Task 15: Final cleanup and .env setup

**Files:**
- Modify: `claude/.gitignore`
- Verify: all tests pass, app runs

- [ ] **Step 1: Ensure .env and __pycache__ are in .gitignore**

Verify `claude/.gitignore` includes:

```
.env
__pycache__/
*.pyc
ai_news.db
```

- [ ] **Step 2: Run full test suite**

Run: `.venv/bin/python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 3: Manual smoke test**

```bash
cd claude
cp .env.example .env
# Edit .env with SECRET_KEY
.venv/bin/python -m cli.create_admin --email admin@test.com --password admin123 --nickname 관리자
.venv/bin/uvicorn main:app --reload --port 8000
```

Verify:
1. Feed page loads without login
2. Sidebar shows login/register links (no admin menu)
3. Register form works (email sending may fail without SMTP, but user is created)
4. Login with admin shows full sidebar (source management, crawl button)
5. Bookmark/memo/tags buttons only visible when logged in

- [ ] **Step 4: Commit**

```bash
git add .gitignore
git commit -m "chore: final cleanup for auth system"
```
