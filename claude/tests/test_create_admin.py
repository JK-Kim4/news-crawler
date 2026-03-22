import pytest
from cli.create_admin import create_admin
from db.models import User


def test_create_admin(db):
    user = create_admin("admin@test.com", "password123", "Admin", db=db)
    assert user.role == "admin"
    assert user.is_verified is True
    assert user.email == "admin@test.com"
    found = db.query(User).filter_by(email="admin@test.com").first()
    assert found is not None


def test_create_admin_duplicate_email(db):
    create_admin("dup@test.com", "pass", "A", db=db)
    with pytest.raises(ValueError, match="already exists"):
        create_admin("dup@test.com", "pass", "B", db=db)
