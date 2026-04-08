from .conftest import login


def test_register_and_login_flow(client):
    register_response = client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "alice123"},
    )
    assert register_response.status_code == 201
    assert register_response.get_json()["user"]["role"] == "user"

    login_response = client.post(
        "/api/auth/login",
        json={"username": "alice", "password": "alice123"},
    )
    assert login_response.status_code == 200
    payload = login_response.get_json()
    assert payload["token"]
    assert payload["user"]["username"] == "alice"


def test_me_and_change_password_flow(client):
    token = login(client, "student", "student123")

    me_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.get_json()["user"]["username"] == "student"

    password_response = client.patch(
        "/api/auth/password",
        json={"old_password": "student123", "new_password": "student456"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert password_response.status_code == 200

    old_login = client.post(
        "/api/auth/login",
        json={"username": "student", "password": "student123"},
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/auth/login",
        json={"username": "student", "password": "student456"},
    )
    assert new_login.status_code == 200

