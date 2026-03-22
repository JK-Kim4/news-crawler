import argparse
from auth.password import hash_password
from db.models import User
from db.session import SessionLocal


def create_admin(email: str, password: str, nickname: str, db=None):
    """Create an admin user. Raises ValueError if email exists."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    try:
        existing = db.query(User).filter_by(email=email).first()
        if existing:
            raise ValueError(f"Email '{email}' already exists.")
        user = User(
            email=email,
            password_hash=hash_password(password),
            nickname=nickname,
            role="admin",
            is_verified=True,
        )
        db.add(user)
        db.commit()
        return user
    finally:
        if close_db:
            db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create admin user")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--nickname", required=True)
    args = parser.parse_args()
    try:
        create_admin(args.email, args.password, args.nickname)
        print(f"Admin user '{args.nickname}' ({args.email}) created successfully.")
    except ValueError as e:
        print(f"Error: {e}")
        exit(1)
