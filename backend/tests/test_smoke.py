import pytest
from fastapi.testclient import TestClient

from app.ai_client import OpenRouterConfigurationError
from app.ai_client import OpenRouterRequestError
from app.ai_client import OpenRouterTimeoutError
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


def test_ai_connectivity_requires_authentication() -> None:
    with TestClient(create_app()) as client:
        response = client.post("/api/ai/connectivity", json={"prompt": "2+2"})
        assert response.status_code == 401


def test_ai_connectivity_success(monkeypatch) -> None:
    monkeypatch.setattr("app.routers.ai.query_openrouter", lambda prompt: "4")

    with TestClient(create_app()) as client:
        client.post(
            "/api/auth/login",
            json={"username": "user", "password": "password"},
        )

        response = client.post("/api/ai/connectivity", json={"prompt": "2+2"})
        assert response.status_code == 200
        payload = response.json()
        assert payload["prompt"] == "2+2"
        assert payload["response"] == "4"
        assert payload["model"] == "openai/gpt-oss-120b"


def test_ai_connectivity_missing_key_returns_error(monkeypatch) -> None:
    def raise_missing_key(_: str) -> str:
        raise OpenRouterConfigurationError("OPENROUTER_API_KEY is not configured")

    monkeypatch.setattr("app.routers.ai.query_openrouter", raise_missing_key)

    with TestClient(create_app()) as client:
        client.post(
            "/api/auth/login",
            json={"username": "user", "password": "password"},
        )

        response = client.post("/api/ai/connectivity", json={"prompt": "2+2"})
        assert response.status_code == 500


def test_ai_connectivity_timeout_returns_504(monkeypatch) -> None:
    def raise_timeout(_: str) -> str:
        raise OpenRouterTimeoutError("OpenRouter request timed out")

    monkeypatch.setattr("app.routers.ai.query_openrouter", raise_timeout)

    with TestClient(create_app()) as client:
        client.post(
            "/api/auth/login",
            json={"username": "user", "password": "password"},
        )

        response = client.post("/api/ai/connectivity", json={"prompt": "2+2"})
        assert response.status_code == 504


def test_ai_connectivity_request_error_returns_502(monkeypatch) -> None:
    def raise_request_error(_: str) -> str:
        raise OpenRouterRequestError("upstream error")

    monkeypatch.setattr("app.routers.ai.query_openrouter", raise_request_error)

    with TestClient(create_app()) as client:
        client.post(
            "/api/auth/login",
            json={"username": "user", "password": "password"},
        )

        response = client.post("/api/ai/connectivity", json={"prompt": "2+2"})
        assert response.status_code == 502


def test_ai_board_action_rejects_invalid_json(monkeypatch) -> None:
    monkeypatch.setattr("app.routers.ai.query_openrouter", lambda _: "not-json")

    with TestClient(create_app()) as client:
        client.post(
            "/api/auth/login",
            json={"username": "user", "password": "password"},
        )

        response = client.post(
            "/api/ai/board-action",
            json={"question": "What should I do next?", "conversation_history": []},
        )
        assert response.status_code == 502


def test_ai_board_action_without_board_update(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.routers.ai.query_openrouter",
        lambda _: '{"assistant_response":"No board change needed.","board_update":null}',
    )

    with TestClient(create_app()) as client:
        client.post(
            "/api/auth/login",
            json={"username": "user", "password": "password"},
        )

        before = client.get("/api/board").json()
        response = client.post(
            "/api/ai/board-action",
            json={"question": "Summarize the board", "conversation_history": []},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["assistant_response"] == "No board change needed."
        assert payload["board_updated"] is False

        after = client.get("/api/board").json()
        assert after == before


def test_ai_board_action_with_board_update_persists(monkeypatch) -> None:
    def fake_query(prompt: str) -> str:
        return (
            '{"assistant_response":"Updated board.",'
            '"board_update":{'
            '"columns":[{"id":"col-backlog","title":"Backlog","cardIds":["card-1","card-2"]},'
            '{"id":"col-discovery","title":"Discovery","cardIds":["card-3"]},'
            '{"id":"col-progress","title":"In Progress","cardIds":["card-4","card-5"]},'
            '{"id":"col-review","title":"Review","cardIds":["card-6"]},'
            '{"id":"col-done","title":"Done","cardIds":["card-7","card-8"]}],'
            '"cards":{'
            '"card-1":{"id":"card-1","title":"AI Updated Title","details":"Draft quarterly themes with impact statements and metrics."},'
            '"card-2":{"id":"card-2","title":"Gather customer signals","details":"Review support tags, sales notes, and churn feedback."},'
            '"card-3":{"id":"card-3","title":"Prototype analytics view","details":"Sketch initial dashboard layout and key drill-downs."},'
            '"card-4":{"id":"card-4","title":"Refine status language","details":"Standardize column labels and tone across the board."},'
            '"card-5":{"id":"card-5","title":"Design card layout","details":"Add hierarchy and spacing for scanning dense lists."},'
            '"card-6":{"id":"card-6","title":"QA micro-interactions","details":"Verify hover, focus, and loading states."},'
            '"card-7":{"id":"card-7","title":"Ship marketing page","details":"Final copy approved and asset pack delivered."},'
            '"card-8":{"id":"card-8","title":"Close onboarding sprint","details":"Document release notes and share internally."}'
            '}}}'
        )

    monkeypatch.setattr("app.routers.ai.query_openrouter", fake_query)

    with TestClient(create_app()) as client:
        client.post(
            "/api/auth/login",
            json={"username": "user", "password": "password"},
        )

        response = client.post(
            "/api/ai/board-action",
            json={"question": "Update title", "conversation_history": []},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["board_updated"] is True
        assert payload["board"]["cards"]["card-1"]["title"] == "AI Updated Title"

        persisted = client.get("/api/board").json()
        assert persisted["cards"]["card-1"]["title"] == "AI Updated Title"


def test_ai_board_action_includes_conversation_history(monkeypatch) -> None:
    captured_prompt = {"value": ""}

    def fake_query(prompt: str) -> str:
        captured_prompt["value"] = prompt
        return '{"assistant_response":"ok","board_update":null}'

    monkeypatch.setattr("app.routers.ai.query_openrouter", fake_query)

    with TestClient(create_app()) as client:
        client.post(
            "/api/auth/login",
            json={"username": "user", "password": "password"},
        )

        response = client.post(
            "/api/ai/board-action",
            json={
                "question": "What next?",
                "conversation_history": [
                    {"role": "user", "content": "We need momentum."},
                    {"role": "assistant", "content": "Focus on review."},
                ],
            },
        )

        assert response.status_code == 200
        assert "We need momentum." in captured_prompt["value"]
        assert "Focus on review." in captured_prompt["value"]
