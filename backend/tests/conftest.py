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


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


def login_default_user(client: TestClient) -> dict:
    """Login with the seeded default user. Returns the response JSON."""
    resp = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    assert resp.status_code == 200
    return resp.json()


def register_and_login(
    client: TestClient,
    username: str = "testuser",
    password: str = "testpass123",
    display_name: str = "",
) -> dict:
    """Register a new user and return the register response JSON."""
    resp = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": password,
            "display_name": display_name,
        },
    )
    assert resp.status_code == 201
    return resp.json()
