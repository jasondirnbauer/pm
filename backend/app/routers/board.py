from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, model_validator

from app.db import get_or_create_board, update_board
from app.routers.auth import require_authenticated_user

router = APIRouter()


class CardPayload(BaseModel):
    id: str
    title: str = Field(max_length=200)
    details: str = Field(max_length=5000)


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


@router.get("/board")
def read_board(username: str = Depends(require_authenticated_user)) -> dict:
    return get_or_create_board(username)


@router.put("/board")
def write_board(
    payload: BoardPayload,
    username: str = Depends(require_authenticated_user),
) -> dict:
    return update_board(username, payload.model_dump())
