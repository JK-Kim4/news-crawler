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
