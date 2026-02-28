from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, model_validator

from app.db import (
    create_board,
    delete_board,
    get_board,
    get_boards_for_user,
    get_default_board_for_user,
    rename_board,
    update_board,
)
from app.routers.auth import SessionUser, require_authenticated_user

router = APIRouter()


class CardLabelPayload(BaseModel):
    id: str
    text: str = Field(max_length=30)
    color: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")


class CardPayload(BaseModel):
    id: str
    title: str = Field(max_length=200)
    details: str = Field(max_length=5000)
    labels: list[CardLabelPayload] = Field(default_factory=list)
    due_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    priority: Literal["none", "low", "medium", "high", "urgent"] = "none"


class ColumnPayload(BaseModel):
    id: str
    title: str
    cardIds: list[str]


class BoardPayload(BaseModel):
    columns: list[ColumnPayload]
    cards: dict[str, CardPayload]

    @model_validator(mode="after")
    def validate_card_references(self) -> "BoardPayload":
        card_keys = set(self.cards.keys())

        for card_key, card in self.cards.items():
            if card.id != card_key:
                raise ValueError("Card key must match card.id")

        for column in self.columns:
            for card_id in column.cardIds:
                if card_id not in card_keys:
                    raise ValueError("Column cardIds must reference known cards")

        return self


# ── Legacy single-board endpoints (backward compatibility) ───────────────


@router.get("/board")
def read_board(user: SessionUser = Depends(require_authenticated_user)) -> dict:
    board = get_default_board_for_user(user.user_id)
    return board["board_json"]


@router.put("/board")
def write_board(
    payload: BoardPayload,
    user: SessionUser = Depends(require_authenticated_user),
) -> dict:
    board = get_default_board_for_user(user.user_id)
    result = update_board(board["id"], user.user_id, payload.model_dump())
    return result["board_json"]


# ── Multi-board CRUD endpoints ───────────────────────────────────────────


@router.get("/boards")
def list_boards(user: SessionUser = Depends(require_authenticated_user)) -> list[dict]:
    return get_boards_for_user(user.user_id)


class CreateBoardRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


@router.post("/boards", status_code=status.HTTP_201_CREATED)
def create_board_endpoint(
    payload: CreateBoardRequest,
    user: SessionUser = Depends(require_authenticated_user),
) -> dict:
    return create_board(user.user_id, payload.name)


@router.get("/boards/{board_id}")
def get_board_endpoint(
    board_id: str,
    user: SessionUser = Depends(require_authenticated_user),
) -> dict:
    board = get_board(board_id, user.user_id)
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found",
        )
    return board


@router.put("/boards/{board_id}")
def update_board_endpoint(
    board_id: str,
    payload: BoardPayload,
    user: SessionUser = Depends(require_authenticated_user),
) -> dict:
    board = get_board(board_id, user.user_id)
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found",
        )
    return update_board(board_id, user.user_id, payload.model_dump())


class RenameBoardRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


@router.patch("/boards/{board_id}")
def rename_board_endpoint(
    board_id: str,
    payload: RenameBoardRequest,
    user: SessionUser = Depends(require_authenticated_user),
) -> dict:
    board = get_board(board_id, user.user_id)
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found",
        )
    return rename_board(board_id, user.user_id, payload.name)


@router.delete("/boards/{board_id}")
def delete_board_endpoint(
    board_id: str,
    user: SessionUser = Depends(require_authenticated_user),
) -> dict:
    board = get_board(board_id, user.user_id)
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found",
        )
    try:
        delete_board(board_id, user.user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return {"status": "ok"}
