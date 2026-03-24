from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.enums import UserRole
from app.models.notification import NotificationPreference
from app.models.user import User


def register_user(db: Session, username: str, email: str, password: str) -> User:
    existing = db.scalar(select(User).where((User.email == email) | (User.username == username)))
    if existing:
        raise ValueError("User already exists")

    user = User(username=username, email=email, password_hash=hash_password(password), role=UserRole.USER)
    db.add(user)
    db.flush()
    db.add(NotificationPreference(user_id=user.id, keywords=[]))
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


def issue_token(user: User) -> str:
    return create_access_token(user.id, user.role.value)

