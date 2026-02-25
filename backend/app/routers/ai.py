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
from app.db import get_or_create_board, update_board
from app.routers.auth import require_authenticated_user
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
        '    "cards": {"card-id": {"id": string, "title": string, "details": string}}\n'
        "  }\n"
        "}\n\n"
        "If no board changes are needed, set board_update to null.\n\n"
        f"Current board JSON:\n{json.dumps(board, ensure_ascii=False)}\n\n"
        f"Conversation history:\n{history_block}\n\n"
        f"User question:\n{question}\n"
    )


@router.post("/ai/connectivity")
def ai_connectivity(
    payload: ConnectivityRequest,
    username: str = Depends(require_authenticated_user),
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
        "user": username,
    }


@router.post("/ai/board-action")
def ai_board_action(
    payload: BoardActionRequest,
    username: str = Depends(require_authenticated_user),
) -> dict:
    current_board = get_or_create_board(username)
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
            detail=f"AI structured output validation failed: {exc}",
        ) from exc

    if structured.board_update is not None:
        next_board = update_board(username, structured.board_update.model_dump())
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
