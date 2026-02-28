from tests.conftest import login_default_user, register_and_login


def test_register_creates_user(client) -> None:
    resp = client.post(
        "/api/auth/register",
        json={"username": "newuser", "password": "secret123", "display_name": "New User"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "newuser"
    assert data["display_name"] == "New User"

    # Session cookie should be set (auto-login)
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["username"] == "newuser"


def test_register_duplicate_username_returns_409(client) -> None:
    register_and_login(client, username="taken")
    client.post("/api/auth/logout")

    resp = client.post(
        "/api/auth/register",
        json={"username": "taken", "password": "anotherpass"},
    )
    assert resp.status_code == 409
    assert "already taken" in resp.json()["detail"]


def test_register_short_username_returns_422(client) -> None:
    resp = client.post(
        "/api/auth/register",
        json={"username": "ab", "password": "secret123"},
    )
    assert resp.status_code == 422


def test_register_short_password_returns_422(client) -> None:
    resp = client.post(
        "/api/auth/register",
        json={"username": "validuser", "password": "short"},
    )
    assert resp.status_code == 422


def test_register_invalid_username_chars_returns_422(client) -> None:
    resp = client.post(
        "/api/auth/register",
        json={"username": "bad user!", "password": "secret123"},
    )
    assert resp.status_code == 422


def test_login_with_seeded_user(client) -> None:
    resp = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == "user"


def test_login_with_registered_user(client) -> None:
    register_and_login(client, username="alice", password="alicepass1")
    client.post("/api/auth/logout")

    resp = client.post(
        "/api/auth/login",
        json={"username": "alice", "password": "alicepass1"},
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"


def test_login_invalid_password_returns_401(client) -> None:
    resp = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "wrongpass"},
    )
    assert resp.status_code == 401


def test_login_nonexistent_user_returns_401(client) -> None:
    resp = client.post(
        "/api/auth/login",
        json={"username": "nonexistent", "password": "whatever"},
    )
    assert resp.status_code == 401


def test_me_returns_user_info(client) -> None:
    login_default_user(client)
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    data = me.json()
    assert data["username"] == "user"
    assert "display_name" in data


def test_me_requires_session(client) -> None:
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_logout_clears_session(client) -> None:
    login_default_user(client)
    client.post("/api/auth/logout")
    me = client.get("/api/auth/me")
    assert me.status_code == 401


def test_update_profile_display_name(client) -> None:
    login_default_user(client)
    resp = client.put("/api/auth/me", json={"display_name": "New Name"})
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "New Name"

    me = client.get("/api/auth/me")
    assert me.json()["display_name"] == "New Name"


def test_change_password_success(client) -> None:
    register_and_login(client, username="pwuser", password="oldpass1")
    resp = client.put(
        "/api/auth/password",
        json={"current_password": "oldpass1", "new_password": "newpass1"},
    )
    assert resp.status_code == 200

    # Logout and login with new password
    client.post("/api/auth/logout")
    resp = client.post(
        "/api/auth/login",
        json={"username": "pwuser", "password": "newpass1"},
    )
    assert resp.status_code == 200


def test_change_password_wrong_current_returns_401(client) -> None:
    login_default_user(client)
    resp = client.put(
        "/api/auth/password",
        json={"current_password": "wrongcurrent", "new_password": "newpass1"},
    )
    assert resp.status_code == 401
