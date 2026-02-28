from secrets import token_urlsafe

import bcrypt
from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from app.db import (
    create_board,
    create_user,
    get_user_by_username,
    update_user_display_name,
    update_user_password,
)

router = APIRouter()

SESSION_COOKIE_NAME = "pm_session"

# token -> {user_id, username, display_name}
sessions: dict[str, dict] = {}


class SessionUser(BaseModel):
    user_id: int
    username: str
    display_name: str = ""


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=6, max_length=128)
    display_name: str = Field(default="", max_length=100)


class UpdateProfileRequest(BaseModel):
    display_name: str = Field(max_length=100)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6, max_length=128)


def get_session_user(request: Request) -> SessionUser | None:
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_token:
        return None
    session_data = sessions.get(session_token)
    if not session_data:
        return None
    return SessionUser(**session_data)


def require_authenticated_user(request: Request) -> SessionUser:
    user = get_session_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user


def _set_session_cookie(response: Response, user: dict) -> str:
    session_token = token_urlsafe(32)
    sessions[session_token] = {
        "user_id": user["id"],
        "username": user["username"],
        "display_name": user.get("display_name", ""),
    }
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        samesite="lax",
        path="/",
        max_age=60 * 60 * 8,
    )
    return session_token


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, response: Response) -> dict:
    existing = get_user_by_username(payload.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    password_hash = bcrypt.hashpw(
        payload.password.encode(), bcrypt.gensalt()
    ).decode()
    user = create_user(payload.username, password_hash, payload.display_name)

    # Create a default board for the new user
    create_board(user["id"], "My Board")

    _set_session_cookie(response, user)
    return {"username": user["username"], "display_name": user["display_name"]}


@router.post("/login")
def login(payload: LoginRequest, response: Response) -> dict:
    user = get_user_by_username(payload.username)
    if not user or not bcrypt.checkpw(
        payload.password.encode(), user["password_hash"].encode()
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    _set_session_cookie(response, user)
    return {"username": user["username"], "display_name": user.get("display_name", "")}


@router.post("/logout")
def logout(request: Request, response: Response) -> dict[str, str]:
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if session_token:
        sessions.pop(session_token, None)

    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return {"status": "ok"}


@router.get("/me")
def me(request: Request) -> dict:
    user = require_authenticated_user(request)
    return {"username": user.username, "display_name": user.display_name}


@router.put("/me")
def update_profile(payload: UpdateProfileRequest, request: Request) -> dict:
    user = require_authenticated_user(request)
    updated = update_user_display_name(user.user_id, payload.display_name)

    # Update session cache
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if session_token and session_token in sessions:
        sessions[session_token]["display_name"] = payload.display_name

    return {"username": updated["username"], "display_name": updated["display_name"]}


@router.put("/password")
def change_password(payload: ChangePasswordRequest, request: Request) -> dict:
    user = require_authenticated_user(request)
    db_user = get_user_by_username(user.username)

    if not db_user or not bcrypt.checkpw(
        payload.current_password.encode(), db_user["password_hash"].encode()
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )

    new_hash = bcrypt.hashpw(
        payload.new_password.encode(), bcrypt.gensalt()
    ).decode()
    update_user_password(user.user_id, new_hash)
    return {"status": "ok"}
