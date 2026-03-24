def test_register_and_login_issue_tokens(client):
    register_response = client.post(
        "/api/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "secret123"},
    )

    assert register_response.status_code == 201
    register_payload = register_response.json()
    assert register_payload["access_token"]
    assert register_payload["user"]["email"] == "alice@example.com"

    login_response = client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "secret123"},
    )

    assert login_response.status_code == 200
    login_payload = login_response.json()
    assert login_payload["access_token"]
    assert login_payload["user"]["username"] == "alice"

