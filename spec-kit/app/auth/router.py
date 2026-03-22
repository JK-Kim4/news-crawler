from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.api.templates import templates
from app.auth.password import hash_password, verify_password
from app.db.models import User
from app.db.session import get_db

router = APIRouter(prefix="/auth")


@router.get("/register", response_class=HTMLResponse)
def get_register(request: Request):
    return templates.TemplateResponse(request, "auth/register.html", {"request": request})


@router.post("/register", response_class=HTMLResponse)
def post_register(
    request: Request,
    email: str = Form(...),
    nickname: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    db: Session = Depends(get_db),
):
    if len(password) < 8:
        return templates.TemplateResponse(request, "auth/register.html",
            {"request": request, "error": "비밀번호는 최소 8자 이상이어야 합니다.", "email": email, "nickname": nickname})

    if password != password_confirm:
        return templates.TemplateResponse(request, "auth/register.html",
            {"request": request, "error": "비밀번호가 일치하지 않습니다.", "email": email, "nickname": nickname})

    existing = db.query(User).filter_by(email=email).first()
    if existing:
        return templates.TemplateResponse(request, "auth/register.html",
            {"request": request, "error": "이미 가입된 이메일입니다.", "email": email, "nickname": nickname})

    user = User(email=email, nickname=nickname, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    return RedirectResponse(url="/auth/login", status_code=303)


@router.get("/login", response_class=HTMLResponse)
def get_login(request: Request):
    return templates.TemplateResponse(request, "auth/login.html", {"request": request})


@router.post("/login")
def post_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter_by(email=email).first()

    if user is None or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(request, "auth/login.html",
            {"request": request, "error": "이메일 또는 비밀번호가 잘못되었습니다.", "email": email})

    if not user.is_active:
        return templates.TemplateResponse(request, "auth/login.html",
            {"request": request, "error": "비활성화된 계정입니다. 관리자에게 문의하세요.", "email": email})

    request.session["user_id"] = user.id
    request.session["user_email"] = user.email
    request.session["user_role"] = user.role
    return RedirectResponse(url="/", status_code=303)


@router.post("/logout")
def post_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)
