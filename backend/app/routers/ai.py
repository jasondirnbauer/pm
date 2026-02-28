import json

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.ai_client import (
    MODEL_NAME,
    OpenRouterConfigurationError,
    OpenRouterRequestError,
    OpenRouterTimeoutError,
    query_openrouter,
)
from app.db import get_board, get_default_board_for_user, update_board
from app.routers.auth import SessionUser, require_authenticated_user
from app.routers.board import BoardPayload

router = APIRouter()


class ConnectivityRequest(BaseModel):
    prompt: str = "2+2"


class ConversationTurn(BaseModel):
    role: str
    content: str


class BoardActionRequest(BaseModel):
    question: str
    conversation_history: list[ConversationTurn] = []
    board_id: str | None = None


class StructuredBoardAction(BaseModel):
    assistant_response: str
    board_update: BoardPayload | None


def _extract_json_block(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        stripped = stripped.removeprefix("json").strip()
    return stripped


def _build_board_action_prompt(
    board: dict,
    question: str,
    conversation_history: list[ConversationTurn],
) -> str:
    history_lines = []
    for turn in conversation_history:
        history_lines.append(f"{turn.role}: {turn.content}")

    history_block = "\n".join(history_lines) if history_lines else "(none)"

    return (
        "You are a project management assistant for a Kanban board.\n"
        "You must respond with valid JSON only and no extra text.\n"
        "Required JSON schema:\n"
        "{\n"
        '  "assistant_response": string,\n'
        '  "board_update": null | {\n'
        '    "columns": [{"id": string, "title": string, "cardIds": [string]}],\n'
        '    "cards": {"card-id": {"id": string, "title": string, "details": string, '
        '"labels": [{"id": string, "text": string, "color": string}], '
        '"due_date": string|null, "priority": "none"|"low"|"medium"|"high"|"urgent"}}\n'
        "  }\n"
        "}\n\n"
        "If no board changes are needed, set board_update to null.\n"
        "Labels, due_date, and priority are optional on cards.\n\n"
        f"Current board JSON:\n{json.dumps(board, ensure_ascii=False)}\n\n"
        f"Conversation history:\n{history_block}\n\n"
        f"User question:\n{question}\n"
    )


@router.post("/ai/connectivity")
def ai_connectivity(
    payload: ConnectivityRequest,
    user: SessionUser = Depends(require_authenticated_user),
) -> dict:
    try:
        answer = query_openrouter(payload.prompt)
    except OpenRouterConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except OpenRouterTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        ) from exc
    except OpenRouterRequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return {
        "model": MODEL_NAME,
        "prompt": payload.prompt,
        "response": answer,
        "user": user.username,
    }


@router.post("/ai/board-action")
def ai_board_action(
    payload: BoardActionRequest,
    user: SessionUser = Depends(require_authenticated_user),
) -> dict:
    if payload.board_id:
        board_record = get_board(payload.board_id, user.user_id)
        if not board_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Board not found",
            )
        current_board = board_record["board_json"]
        board_id = payload.board_id
    else:
        board_record = get_default_board_for_user(user.user_id)
        current_board = board_record["board_json"]
        board_id = board_record["id"]

    prompt = _build_board_action_prompt(
        board=current_board,
        question=payload.question,
        conversation_history=payload.conversation_history,
    )

    try:
        raw_response = query_openrouter(prompt)
    except OpenRouterConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except OpenRouterTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        ) from exc
    except OpenRouterRequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    try:
        parsed = json.loads(_extract_json_block(raw_response))
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI response was not valid JSON",
        ) from exc

    try:
        structured = StructuredBoardAction.model_validate(parsed)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI structured output validation failed",
        ) from exc

    if structured.board_update is not None:
        result = update_board(board_id, user.user_id, structured.board_update.model_dump())
        next_board = result["board_json"]
        board_updated = True
    else:
        next_board = current_board
        board_updated = False

    return {
        "model": MODEL_NAME,
        "assistant_response": structured.assistant_response,
        "board": next_board,
        "board_updated": board_updated,
    }
