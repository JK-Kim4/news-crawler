from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User


def test_admin_can_trigger_crawl_job(client, db_session, monkeypatch):
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=hash_password("secret123"),
        role=UserRole.ADMIN,
    )
    db_session.add(admin)
    db_session.commit()

    from app.tasks import crawl as crawl_tasks

    class DummyResult:
        id = "task-123"

    def fake_delay(source_ids, trigger):
        assert trigger == "manual"
        return DummyResult()

    monkeypatch.setattr(crawl_tasks.trigger_manual_crawl, "delay", fake_delay)

    login_response = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "secret123"})
    token = login_response.json()["access_token"]
    response = client.post(
        "/api/admin/crawl/run",
        json={"source_ids": []},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "queued", "task_id": "task-123"}

