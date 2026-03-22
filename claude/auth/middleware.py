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
