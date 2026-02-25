import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.routers.auth import sessions


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "pm.db"))
    sessions.clear()
    yield
    sessions.clear()


def test_health_endpoint() -> None:
    client = TestClient(create_app())
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_hello_endpoint() -> None:
    client = TestClient(create_app())
    response = client.get("/api/hello")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello from FastAPI"}


def test_root_serves_static_html() -> None:
    client = TestClient(create_app())
    response = client.get("/")

    assert response.status_code == 200
    assert "<html" in response.text.lower()


def test_auth_login_and_me_flow() -> None:
    with TestClient(create_app()) as client:
        login_response = client.post(
            "/api/auth/login",
            json={"username": "user", "password": "password"},
        )

        assert login_response.status_code == 200
        assert login_response.json() == {"username": "user"}

        me_response = client.get("/api/auth/me")
        assert me_response.status_code == 200
        assert me_response.json() == {"username": "user"}


def test_auth_rejects_invalid_credentials() -> None:
    with TestClient(create_app()) as client:
        response = client.post(
            "/api/auth/login",
            json={"username": "bad", "password": "creds"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid username or password"


def test_auth_me_requires_session() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/auth/me")
        assert response.status_code == 401


def test_auth_logout_clears_session() -> None:
    with TestClient(create_app()) as client:
        client.post(
            "/api/auth/login",
            json={"username": "user", "password": "password"},
        )

        logout_response = client.post("/api/auth/logout")
        assert logout_response.status_code == 200

        me_response = client.get("/api/auth/me")
        assert me_response.status_code == 401


def test_board_requires_authentication() -> None:
    with TestClient(create_app()) as client:
        get_response = client.get("/api/board")
        put_response = client.put("/api/board", json={})

        assert get_response.status_code == 401
        assert put_response.status_code == 401


def test_board_returns_default_for_new_user() -> None:
    with TestClient(create_app()) as client:
        client.post(
            "/api/auth/login",
            json={"username": "user", "password": "password"},
        )

        response = client.get("/api/board")

        assert response.status_code == 200
        payload = response.json()
        assert "columns" in payload
        assert "cards" in payload
        assert len(payload["columns"]) == 5


def test_board_update_roundtrip() -> None:
    with TestClient(create_app()) as client:
        client.post(
            "/api/auth/login",
            json={"username": "user", "password": "password"},
        )

        board = client.get("/api/board").json()
        board["cards"]["card-1"]["title"] = "Updated from API"

        write_response = client.put("/api/board", json=board)
        assert write_response.status_code == 200

        read_back = client.get("/api/board")
        assert read_back.status_code == 200
        assert read_back.json()["cards"]["card-1"]["title"] == "Updated from API"


def test_board_update_rejects_invalid_payload() -> None:
    with TestClient(create_app()) as client:
        client.post(
            "/api/auth/login",
            json={"username": "user", "password": "password"},
        )

        invalid_payload = {
            "columns": [
                {
                    "id": "col-1",
                    "title": "Only",
                    "cardIds": ["missing-card"],
                }
            ],
            "cards": {},
        }

        response = client.put("/api/board", json=invalid_payload)
        assert response.status_code == 422


def test_board_persists_across_app_instances() -> None:
    first_app = create_app()
    with TestClient(first_app) as first_client:
        first_client.post(
            "/api/auth/login",
            json={"username": "user", "password": "password"},
        )
        board = first_client.get("/api/board").json()
        board["cards"]["card-2"]["title"] = "Persisted value"
        first_client.put("/api/board", json=board)

    second_app = create_app()
    with TestClient(second_app) as second_client:
        second_client.post(
            "/api/auth/login",
            json={"username": "user", "password": "password"},
        )
        second_board = second_client.get("/api/board").json()
        assert second_board["cards"]["card-2"]["title"] == "Persisted value"
