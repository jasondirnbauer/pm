from secrets import token_urlsafe

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel

router = APIRouter()

SESSION_COOKIE_NAME = "pm_session"
VALID_USERNAME = "user"
VALID_PASSWORD = "password"

sessions: dict[str, str] = {}


class LoginRequest(BaseModel):
    username: str
    password: str


def get_session_user(request: Request) -> str | None:
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_token:
        return None
    return sessions.get(session_token)


def require_authenticated_user(request: Request) -> str:
    username = get_session_user(request)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    return username


@router.post("/login")
def login(payload: LoginRequest, response: Response) -> dict[str, str]:
    if payload.username != VALID_USERNAME or payload.password != VALID_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    session_token = token_urlsafe(32)
    sessions[session_token] = payload.username

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        samesite="lax",
        path="/",
        max_age=60 * 60 * 8,
    )
    return {"username": payload.username}


@router.post("/logout")
def logout(request: Request, response: Response) -> dict[str, str]:
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if session_token:
        sessions.pop(session_token, None)

    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return {"status": "ok"}


@router.get("/me")
def me(request: Request) -> dict[str, str]:
    username = require_authenticated_user(request)
    return {"username": username}
