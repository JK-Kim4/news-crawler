from fastapi import Request


class LoginRequired(Exception):
    pass


def get_current_user(request: Request):
    return getattr(getattr(request, "state", None), "user", None)


def require_login(request: Request):
    user = get_current_user(request)
    if user is None:
        raise LoginRequired()
    return user


def require_admin(request: Request):
    user = require_login(request)
    if user.role != "admin":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    return user
