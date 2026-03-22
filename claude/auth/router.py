import logging
import os
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from api.templates import templates
from auth.password import hash_password, verify_password
from db.models import User
from db.session import get_db

router = APIRouter(prefix="/auth")
logger = logging.getLogger(__name__)

# Mail sender — module-level for easy mocking in tests
_mail_sender = None


def _get_mail_sender():
    global _mail_sender
    if _mail_sender is None:
        from auth.mail import SmtpMailSender
        _mail_sender = SmtpMailSender(
            host=os.getenv("SMTP_HOST", ""),
            port=int(os.getenv("SMTP_PORT", "587")),
            user=os.getenv("SMTP_USER", ""),
            password=os.getenv("SMTP_PASSWORD", ""),
            sender_email=os.getenv("SMTP_FROM", ""),
        )
    return _mail_sender


def _send_verification_email(email: str, token: str):
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    link = f"{base_url}/auth/verify?token={token}"
    _get_mail_sender().send(
        to=email,
        subject="AI Archive 이메일 인증",
        body=f"아래 링크를 클릭하면 가입이 완료됩니다:\n\n{link}",
    )


def _send_reset_email(email: str, token: str):
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    link = f"{base_url}/auth/reset-password?token={token}"
    _get_mail_sender().send(
        to=email,
        subject="AI Archive 비밀번호 재설정",
        body=f"아래 링크를 클릭하면 비밀번호를 재설정할 수 있습니다:\n\n{link}",
    )


# ──────────────────────────────────────────────
# 1. GET /auth/register — registration form page
# ──────────────────────────────────────────────
@router.get("/register", response_class=HTMLResponse)
def get_register(request: Request):
    return templates.TemplateResponse(request, "auth/register.html", {"request": request})


# ──────────────────────────────────────────────
# 2. POST /auth/register — create user, send verification email
# ──────────────────────────────────────────────
@router.post("/register", response_class=HTMLResponse)
def post_register(
    request: Request,
    email: str = Form(...),
    nickname: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    db: Session = Depends(get_db),
):
    # Validate password length
    if len(password) < 8:
        return templates.TemplateResponse(
            request,
            "auth/register.html",
            {"request": request, "error": "비밀번호는 최소 8자 이상이어야 합니다.", "email": email, "nickname": nickname},
        )

    # Validate password match
    if password != password_confirm:
        return templates.TemplateResponse(
            request,
            "auth/register.html",
            {"request": request, "error": "비밀번호가 일치하지 않습니다.", "email": email, "nickname": nickname},
        )

    existing = db.query(User).filter_by(email=email).first()

    if existing:
        if existing.is_verified:
            return templates.TemplateResponse(
                request,
                "auth/register.html",
                {"request": request, "error": "이미 가입된 이메일입니다.", "email": email, "nickname": nickname},
            )
        # Not yet verified: regenerate token and resend
        token = str(uuid.uuid4())
        existing.verify_token = token
        existing.verify_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        existing.password_hash = hash_password(password)
        db.commit()
        _send_verification_email(email, token)
        return templates.TemplateResponse(
            request,
            "auth/verify_pending.html",
            {"request": request, "email": email},
        )

    # Create new user
    token = str(uuid.uuid4())
    user = User(
        email=email,
        nickname=nickname,
        password_hash=hash_password(password),
        is_verified=False,
        verify_token=token,
        verify_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(user)
    db.commit()
    _send_verification_email(email, token)
    return templates.TemplateResponse(
        request,
        "auth/verify_pending.html",
        {"request": request, "email": email},
    )


# ──────────────────────────────────────────────
# 3. GET /auth/verify?token=xxx — verify email token
# ──────────────────────────────────────────────
@router.get("/verify")
def get_verify(token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(verify_token=token).first()

    if user is None:
        return HTMLResponse(
            "<h1>인증 오류</h1><p>유효하지 않은 인증 링크입니다.</p>",
            status_code=200,
        )

    now = datetime.now(timezone.utc)
    expires = user.verify_token_expires_at
    if expires is not None and expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if expires is None or now > expires:
        return HTMLResponse(
            "<h1>인증 오류</h1><p>인증 링크가 만료되었습니다. 재발송을 요청해 주세요.</p>",
            status_code=200,
        )

    user.is_verified = True
    user.verify_token = None
    user.verify_token_expires_at = None
    db.commit()
    return RedirectResponse(url="/auth/login", status_code=303)


# ──────────────────────────────────────────────
# 4. GET /auth/login — login form page
# ──────────────────────────────────────────────
@router.get("/login", response_class=HTMLResponse)
def get_login(request: Request):
    return templates.TemplateResponse(request, "auth/login.html", {"request": request})


# ──────────────────────────────────────────────
# 5. POST /auth/login — verify credentials, check is_verified, set session
# ──────────────────────────────────────────────
@router.post("/login")
def post_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter_by(email=email).first()

    if user is None or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {"request": request, "error": "이메일 또는 비밀번호가 잘못되었습니다.", "email": email},
        )

    if not user.is_verified:
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {"request": request, "error": "이메일 인증이 완료되지 않았습니다. 이메일을 확인해 주세요.", "email": email},
        )

    request.session["user_id"] = user.id
    request.session["user_email"] = user.email
    request.session["user_role"] = user.role
    return RedirectResponse(url="/", status_code=303)


# ──────────────────────────────────────────────
# 6. POST /auth/logout — clear session, redirect to /
# ──────────────────────────────────────────────
@router.post("/logout")
def post_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


# ──────────────────────────────────────────────
# 7. POST /auth/resend-verification — regenerate token, resend email
# ──────────────────────────────────────────────
@router.post("/resend-verification", response_class=HTMLResponse)
def post_resend_verification(
    request: Request,
    email: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter_by(email=email).first()

    if user is None or user.is_verified:
        return templates.TemplateResponse(
            request,
            "auth/verify_pending.html",
            {"request": request, "email": email},
        )

    token = str(uuid.uuid4())
    user.verify_token = token
    user.verify_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    db.commit()
    _send_verification_email(email, token)
    return templates.TemplateResponse(
        request,
        "auth/verify_pending.html",
        {"request": request, "email": email},
    )


# ──────────────────────────────────────────────
# 8. GET /auth/forgot-password — password reset form
# ──────────────────────────────────────────────
@router.get("/forgot-password", response_class=HTMLResponse)
def get_forgot_password(request: Request):
    return templates.TemplateResponse(request, "auth/forgot_password.html", {"request": request})


# ──────────────────────────────────────────────
# 9. POST /auth/forgot-password — generate reset token (1h), send email
#    Always show success (prevent enumeration)
# ──────────────────────────────────────────────
@router.post("/forgot-password", response_class=HTMLResponse)
def post_forgot_password(
    request: Request,
    email: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter_by(email=email).first()

    if user is not None:
        token = str(uuid.uuid4())
        user.reset_token = token
        user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        db.commit()
        _send_reset_email(email, token)

    # Always return success to prevent email enumeration
    return templates.TemplateResponse(
        request,
        "auth/forgot_password.html",
        {"request": request, "sent": True},
    )


# ──────────────────────────────────────────────
# 10. GET /auth/reset-password?token=xxx — new password form
# ──────────────────────────────────────────────
@router.get("/reset-password", response_class=HTMLResponse)
def get_reset_password(request: Request, token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(reset_token=token).first()

    if user is None:
        return HTMLResponse(
            "<h1>오류</h1><p>유효하지 않은 비밀번호 재설정 링크입니다.</p>",
            status_code=200,
        )

    now = datetime.now(timezone.utc)
    expires = user.reset_token_expires_at
    if expires is not None and expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if expires is None or now > expires:
        return HTMLResponse(
            "<h1>오류</h1><p>비밀번호 재설정 링크가 만료되었습니다.</p>",
            status_code=200,
        )

    return templates.TemplateResponse(
        request,
        "auth/reset_password.html",
        {"request": request, "token": token},
    )


# ──────────────────────────────────────────────
# 11. POST /auth/reset-password — validate token, update password
# ──────────────────────────────────────────────
@router.post("/reset-password")
def post_reset_password(
    request: Request,
    token: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    db: Session = Depends(get_db),
):
    if len(password) < 8:
        return templates.TemplateResponse(
            request,
            "auth/reset_password.html",
            {"request": request, "token": token, "error": "비밀번호는 최소 8자 이상이어야 합니다."},
        )

    if password != password_confirm:
        return templates.TemplateResponse(
            request,
            "auth/reset_password.html",
            {"request": request, "token": token, "error": "비밀번호가 일치하지 않습니다."},
        )

    user = db.query(User).filter_by(reset_token=token).first()

    if user is None:
        return HTMLResponse(
            "<h1>오류</h1><p>유효하지 않은 비밀번호 재설정 링크입니다.</p>",
            status_code=200,
        )

    now = datetime.now(timezone.utc)
    expires = user.reset_token_expires_at
    if expires is not None and expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if expires is None or now > expires:
        return HTMLResponse(
            "<h1>오류</h1><p>비밀번호 재설정 링크가 만료되었습니다.</p>",
            status_code=200,
        )

    user.password_hash = hash_password(password)
    user.reset_token = None
    user.reset_token_expires_at = None
    db.commit()
    return RedirectResponse(url="/auth/login", status_code=303)
