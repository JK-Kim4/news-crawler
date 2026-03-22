"""Seed script to create a default admin account."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal, init_db
from app.db.models import User
from app.auth.password import hash_password


def seed_admin(email="admin@example.com", password="admin123", nickname="Admin"):
    init_db()
    db = SessionLocal()
    try:
        existing = db.query(User).filter_by(email=email).first()
        if existing:
            print(f"Admin account already exists: {email}")
            return
        admin = User(
            email=email,
            password_hash=hash_password(password),
            nickname=nickname,
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"Admin account created: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
