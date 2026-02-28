from app.ai_client import (
    OpenRouterConfigurationError,
    OpenRouterRequestError,
    OpenRouterTimeoutError,
)
from tests.conftest import login_default_user


def test_ai_connectivity_requires_authentication(client) -> None:
    resp = client.post("/api/ai/connectivity", json={"prompt": "2+2"})
    assert resp.status_code == 401


def test_ai_connectivity_success(client, monkeypatch) -> None:
    monkeypatch.setattr("app.routers.ai.query_openrouter", lambda prompt: "4")
    login_default_user(client)

    resp = client.post("/api/ai/connectivity", json={"prompt": "2+2"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["prompt"] == "2+2"
    assert data["response"] == "4"
    assert data["model"] == "openai/gpt-oss-120b"


def test_ai_connectivity_missing_key_returns_500(client, monkeypatch) -> None:
    def raise_missing_key(_):
        raise OpenRouterConfigurationError("OPENROUTER_API_KEY is not configured")

    monkeypatch.setattr("app.routers.ai.query_openrouter", raise_missing_key)
    login_default_user(client)

    resp = client.post("/api/ai/connectivity", json={"prompt": "2+2"})
    assert resp.status_code == 500


def test_ai_connectivity_timeout_returns_504(client, monkeypatch) -> None:
    def raise_timeout(_):
        raise OpenRouterTimeoutError("OpenRouter request timed out")

    monkeypatch.setattr("app.routers.ai.query_openrouter", raise_timeout)
    login_default_user(client)

    resp = client.post("/api/ai/connectivity", json={"prompt": "2+2"})
    assert resp.status_code == 504


def test_ai_connectivity_request_error_returns_502(client, monkeypatch) -> None:
    def raise_request_error(_):
        raise OpenRouterRequestError("upstream error")

    monkeypatch.setattr("app.routers.ai.query_openrouter", raise_request_error)
    login_default_user(client)

    resp = client.post("/api/ai/connectivity", json={"prompt": "2+2"})
    assert resp.status_code == 502


def test_ai_board_action_rejects_invalid_json(client, monkeypatch) -> None:
    monkeypatch.setattr("app.routers.ai.query_openrouter", lambda _: "not-json")
    login_default_user(client)

    resp = client.post(
        "/api/ai/board-action",
        json={"question": "What should I do?", "conversation_history": []},
    )
    assert resp.status_code == 502


def test_ai_board_action_without_board_update(client, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.routers.ai.query_openrouter",
        lambda _: '{"assistant_response":"No change.","board_update":null}',
    )
    login_default_user(client)

    before = client.get("/api/board").json()
    resp = client.post(
        "/api/ai/board-action",
        json={"question": "Summarize", "conversation_history": []},
    )
    assert resp.status_code == 200
    assert resp.json()["board_updated"] is False

    after = client.get("/api/board").json()
    assert after == before


def test_ai_board_action_with_board_update_persists(client, monkeypatch) -> None:
    def fake_query(prompt):
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
    login_default_user(client)

    resp = client.post(
        "/api/ai/board-action",
        json={"question": "Update title", "conversation_history": []},
    )
    assert resp.status_code == 200
    assert resp.json()["board_updated"] is True
    assert resp.json()["board"]["cards"]["card-1"]["title"] == "AI Updated Title"

    persisted = client.get("/api/board").json()
    assert persisted["cards"]["card-1"]["title"] == "AI Updated Title"


def test_ai_board_action_includes_conversation_history(client, monkeypatch) -> None:
    captured = {"value": ""}

    def fake_query(prompt):
        captured["value"] = prompt
        return '{"assistant_response":"ok","board_update":null}'

    monkeypatch.setattr("app.routers.ai.query_openrouter", fake_query)
    login_default_user(client)

    resp = client.post(
        "/api/ai/board-action",
        json={
            "question": "What next?",
            "conversation_history": [
                {"role": "user", "content": "We need momentum."},
                {"role": "assistant", "content": "Focus on review."},
            ],
        },
    )
    assert resp.status_code == 200
    assert "We need momentum." in captured["value"]
    assert "Focus on review." in captured["value"]


def test_ai_board_action_with_board_id(client, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.routers.ai.query_openrouter",
        lambda _: '{"assistant_response":"ok","board_update":null}',
    )
    login_default_user(client)

    boards = client.get("/api/boards").json()
    board_id = boards[0]["id"]

    resp = client.post(
        "/api/ai/board-action",
        json={
            "question": "Summarize",
            "conversation_history": [],
            "board_id": board_id,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["assistant_response"] == "ok"


def test_ai_board_action_with_invalid_board_id_returns_404(client, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.routers.ai.query_openrouter",
        lambda _: '{"assistant_response":"ok","board_update":null}',
    )
    login_default_user(client)

    resp = client.post(
        "/api/ai/board-action",
        json={
            "question": "Summarize",
            "conversation_history": [],
            "board_id": "board-nonexistent",
        },
    )
    assert resp.status_code == 404
