import type { BoardData, BoardDetail, BoardSummary } from "./kanban";

const JSON_HEADERS = { "Content-Type": "application/json" };
const CREDS: RequestCredentials = "same-origin";

async function apiFetch(url: string, init?: RequestInit): Promise<Response> {
  return fetch(url, { credentials: CREDS, ...init });
}

// ── Auth ────────────────────────────────────────────────────────────────

export type AuthUser = {
  username: string;
  display_name: string;
};

export async function authMe(): Promise<AuthUser | null> {
  const resp = await apiFetch("/api/auth/me");
  if (!resp.ok) return null;
  return resp.json();
}

export async function authLogin(
  username: string,
  password: string
): Promise<AuthUser> {
  const resp = await apiFetch("/api/auth/login", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ username, password }),
  });
  if (!resp.ok) {
    const detail = await resp.json().catch(() => null);
    throw new Error(detail?.detail ?? "Invalid username or password");
  }
  return resp.json();
}

export async function authRegister(
  username: string,
  password: string,
  display_name: string
): Promise<AuthUser> {
  const resp = await apiFetch("/api/auth/register", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ username, password, display_name }),
  });
  if (!resp.ok) {
    const detail = await resp.json().catch(() => null);
    throw new Error(detail?.detail ?? "Registration failed");
  }
  return resp.json();
}

export async function authLogout(): Promise<void> {
  await apiFetch("/api/auth/logout", { method: "POST" });
}

// ── Boards ──────────────────────────────────────────────────────────────

export async function fetchBoards(): Promise<BoardSummary[]> {
  const resp = await apiFetch("/api/boards");
  if (!resp.ok) throw new Error("Failed to load boards");
  return resp.json();
}

export async function fetchBoard(boardId: string): Promise<BoardDetail> {
  const resp = await apiFetch(`/api/boards/${boardId}`);
  if (!resp.ok) throw new Error("Failed to load board");
  return resp.json();
}

export async function createBoard(name: string): Promise<BoardDetail> {
  const resp = await apiFetch("/api/boards", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ name }),
  });
  if (!resp.ok) throw new Error("Failed to create board");
  return resp.json();
}

export async function updateBoardData(
  boardId: string,
  data: BoardData
): Promise<void> {
  await apiFetch(`/api/boards/${boardId}`, {
    method: "PUT",
    headers: JSON_HEADERS,
    body: JSON.stringify(data),
  });
}

export async function renameBoard(
  boardId: string,
  name: string
): Promise<void> {
  await apiFetch(`/api/boards/${boardId}`, {
    method: "PATCH",
    headers: JSON_HEADERS,
    body: JSON.stringify({ name }),
  });
}

export async function deleteBoard(boardId: string): Promise<void> {
  const resp = await apiFetch(`/api/boards/${boardId}`, {
    method: "DELETE",
  });
  if (!resp.ok) {
    const detail = await resp.json().catch(() => null);
    throw new Error(detail?.detail ?? "Failed to delete board");
  }
}
