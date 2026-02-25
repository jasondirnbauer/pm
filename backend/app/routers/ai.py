from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.ai_client import (
    MODEL_NAME,
    OpenRouterConfigurationError,
    OpenRouterRequestError,
    OpenRouterTimeoutError,
    query_openrouter,
)
from app.routers.auth import require_authenticated_user

router = APIRouter()


class ConnectivityRequest(BaseModel):
    prompt: str = "2+2"


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
