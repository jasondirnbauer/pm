from fastapi.testclient import TestClient

from app.main import create_app


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
