from .conftest import login


def test_admin_can_list_and_update_users(client):
    token = login(client, "admin", "admin123456")

    list_response = client.get("/api/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert list_response.status_code == 200
    users = list_response.get_json()["users"]
    assert len(users) >= 2

    target_user = next(user for user in users if user["username"] == "student")

    role_response = client.patch(
        f"/api/admin/users/{target_user['id']}/role",
        json={"role": "admin"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert role_response.status_code == 200
    assert role_response.get_json()["user"]["role"] == "admin"

    status_response = client.patch(
        f"/api/admin/users/{target_user['id']}/status",
        json={"status": "disabled"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert status_response.status_code == 200
    assert status_response.get_json()["user"]["status"] == "disabled"


def test_non_admin_cannot_access_admin_api(client):
    token = login(client, "student", "student123")

    response = client.get("/api/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403

