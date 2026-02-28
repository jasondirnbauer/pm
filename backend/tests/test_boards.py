from fastapi.testclient import TestClient

from app.main import create_app
from tests.conftest import login_default_user, register_and_login


def test_list_boards_returns_default_after_login(client) -> None:
    login_default_user(client)
    resp = client.get("/api/boards")
    assert resp.status_code == 200
    boards = resp.json()
    assert len(boards) >= 1
    assert boards[0]["name"] == "My Board"


def test_create_board(client) -> None:
    login_default_user(client)
    resp = client.post("/api/boards", json={"name": "Sprint 1"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Sprint 1"
    assert "board_json" in data
    assert len(data["board_json"]["columns"]) == 5  # default template

    boards = client.get("/api/boards").json()
    assert len(boards) == 2


def test_create_board_with_empty_name_returns_422(client) -> None:
    login_default_user(client)
    resp = client.post("/api/boards", json={"name": ""})
    assert resp.status_code == 422


def test_get_board_by_id(client) -> None:
    login_default_user(client)
    boards = client.get("/api/boards").json()
    board_id = boards[0]["id"]

    resp = client.get(f"/api/boards/{board_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == board_id
    assert "board_json" in data
    assert "columns" in data["board_json"]


def test_get_board_not_found_returns_404(client) -> None:
    login_default_user(client)
    resp = client.get("/api/boards/board-nonexistent")
    assert resp.status_code == 404


def test_get_board_owned_by_other_user_returns_404(client) -> None:
    # Register user1 and get their board
    register_and_login(client, username="user1", password="pass1234")
    boards = client.get("/api/boards").json()
    user1_board_id = boards[0]["id"]
    client.post("/api/auth/logout")

    # Register user2 and try to access user1's board
    register_and_login(client, username="user2", password="pass1234")
    resp = client.get(f"/api/boards/{user1_board_id}")
    assert resp.status_code == 404


def test_update_board_data(client) -> None:
    login_default_user(client)
    boards = client.get("/api/boards").json()
    board_id = boards[0]["id"]

    board = client.get(f"/api/boards/{board_id}").json()
    board_json = board["board_json"]
    board_json["cards"]["card-1"]["title"] = "Updated via multi-board API"

    resp = client.put(f"/api/boards/{board_id}", json=board_json)
    assert resp.status_code == 200
    assert resp.json()["board_json"]["cards"]["card-1"]["title"] == "Updated via multi-board API"


def test_update_board_with_invalid_payload_returns_422(client) -> None:
    login_default_user(client)
    boards = client.get("/api/boards").json()
    board_id = boards[0]["id"]

    invalid = {
        "columns": [{"id": "col-1", "title": "Only", "cardIds": ["missing"]}],
        "cards": {},
    }
    resp = client.put(f"/api/boards/{board_id}", json=invalid)
    assert resp.status_code == 422


def test_rename_board(client) -> None:
    login_default_user(client)
    boards = client.get("/api/boards").json()
    board_id = boards[0]["id"]

    resp = client.patch(f"/api/boards/{board_id}", json={"name": "Renamed Board"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed Board"

    updated_boards = client.get("/api/boards").json()
    assert updated_boards[0]["name"] == "Renamed Board"


def test_delete_board(client) -> None:
    login_default_user(client)
    # Create a second board so we can delete one
    client.post("/api/boards", json={"name": "Temp Board"})
    boards = client.get("/api/boards").json()
    assert len(boards) == 2

    resp = client.delete(f"/api/boards/{boards[1]['id']}")
    assert resp.status_code == 200

    boards = client.get("/api/boards").json()
    assert len(boards) == 1


def test_delete_last_board_returns_409(client) -> None:
    login_default_user(client)
    boards = client.get("/api/boards").json()
    assert len(boards) == 1

    resp = client.delete(f"/api/boards/{boards[0]['id']}")
    assert resp.status_code == 409


def test_legacy_board_endpoint_still_works(client) -> None:
    login_default_user(client)
    resp = client.get("/api/board")
    assert resp.status_code == 200
    data = resp.json()
    assert "columns" in data
    assert len(data["columns"]) == 5


def test_legacy_board_put_endpoint_still_works(client) -> None:
    login_default_user(client)
    board = client.get("/api/board").json()
    board["cards"]["card-1"]["title"] = "Legacy update"
    resp = client.put("/api/board", json=board)
    assert resp.status_code == 200
    assert resp.json()["cards"]["card-1"]["title"] == "Legacy update"


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


def test_multiple_users_have_independent_boards(client) -> None:
    register_and_login(client, username="alice", password="alicepass1")
    boards_a = client.get("/api/boards").json()
    assert len(boards_a) == 1
    client.post("/api/auth/logout")

    register_and_login(client, username="bob", password="bobpass123")
    boards_b = client.get("/api/boards").json()
    assert len(boards_b) == 1
    assert boards_b[0]["id"] != boards_a[0]["id"]


def test_board_requires_authentication(client) -> None:
    assert client.get("/api/board").status_code == 401
    assert client.put("/api/board", json={}).status_code == 401
    assert client.get("/api/boards").status_code == 401
    assert client.post("/api/boards", json={"name": "x"}).status_code == 401


def test_board_with_enhanced_card_fields(client) -> None:
    login_default_user(client)
    boards = client.get("/api/boards").json()
    board_id = boards[0]["id"]

    board = client.get(f"/api/boards/{board_id}").json()["board_json"]
    board["cards"]["card-1"]["labels"] = [
        {"id": "lbl-1", "text": "Bug", "color": "#ef4444"}
    ]
    board["cards"]["card-1"]["due_date"] = "2026-03-15"
    board["cards"]["card-1"]["priority"] = "high"

    resp = client.put(f"/api/boards/{board_id}", json=board)
    assert resp.status_code == 200
    card = resp.json()["board_json"]["cards"]["card-1"]
    assert card["labels"][0]["text"] == "Bug"
    assert card["due_date"] == "2026-03-15"
    assert card["priority"] == "high"


def test_board_rejects_invalid_label_color(client) -> None:
    login_default_user(client)
    boards = client.get("/api/boards").json()
    board_id = boards[0]["id"]

    board = client.get(f"/api/boards/{board_id}").json()["board_json"]
    board["cards"]["card-1"]["labels"] = [
        {"id": "lbl-1", "text": "Bug", "color": "not-hex"}
    ]
    resp = client.put(f"/api/boards/{board_id}", json=board)
    assert resp.status_code == 422


def test_board_rejects_invalid_priority(client) -> None:
    login_default_user(client)
    boards = client.get("/api/boards").json()
    board_id = boards[0]["id"]

    board = client.get(f"/api/boards/{board_id}").json()["board_json"]
    board["cards"]["card-1"]["priority"] = "critical"  # invalid value
    resp = client.put(f"/api/boards/{board_id}", json=board)
    assert resp.status_code == 422
