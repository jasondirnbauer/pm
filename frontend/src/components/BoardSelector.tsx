"use client";

import { useState } from "react";
import type { BoardSummary } from "@/lib/kanban";

type BoardSelectorProps = {
  boards: BoardSummary[];
  activeBoardId: string | null;
  onSelectBoard: (boardId: string) => void;
  onCreateBoard: (name: string) => void;
  onRenameBoard: (boardId: string, name: string) => void;
  onDeleteBoard: (boardId: string) => void;
};

export const BoardSelector = ({
  boards,
  activeBoardId,
  onSelectBoard,
  onCreateBoard,
  onRenameBoard,
  onDeleteBoard,
}: BoardSelectorProps) => {
  const [isCreating, setIsCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");

  const handleCreate = () => {
    const name = newName.trim();
    if (!name) return;
    onCreateBoard(name);
    setNewName("");
    setIsCreating(false);
  };

  const handleRenameStart = (board: BoardSummary) => {
    setRenamingId(board.id);
    setRenameValue(board.name);
  };

  const handleRenameSubmit = () => {
    if (renamingId && renameValue.trim()) {
      onRenameBoard(renamingId, renameValue.trim());
    }
    setRenamingId(null);
  };

  return (
    <div className="flex flex-wrap items-center gap-2">
      {boards.map((board) => (
        <div key={board.id} className="group flex items-center">
          {renamingId === board.id ? (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleRenameSubmit();
              }}
              className="flex items-center gap-1"
            >
              <input
                value={renameValue}
                onChange={(e) => setRenameValue(e.target.value)}
                className="w-28 rounded-lg border border-[var(--stroke)] px-2 py-1 text-xs text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)]"
                autoFocus
                maxLength={100}
                onBlur={handleRenameSubmit}
                aria-label="Board name"
              />
            </form>
          ) : (
            <button
              type="button"
              onClick={() => onSelectBoard(board.id)}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                board.id === activeBoardId
                  ? "bg-[var(--secondary-purple)] text-white"
                  : "bg-white border border-[var(--stroke)] text-[var(--navy-dark)] hover:border-[var(--primary-blue)]"
              }`}
            >
              {board.name}
            </button>
          )}

          {board.id === activeBoardId && renamingId !== board.id && (
            <div className="ml-1 flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition">
              <button
                type="button"
                onClick={() => handleRenameStart(board)}
                className="rounded p-1 text-[var(--gray-text)] hover:text-[var(--navy-dark)]"
                aria-label={`Rename ${board.name}`}
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" /><path d="m15 5 4 4" /></svg>
              </button>
              {boards.length > 1 && (
                <button
                  type="button"
                  onClick={() => onDeleteBoard(board.id)}
                  className="rounded p-1 text-[var(--gray-text)] hover:text-red-500"
                  aria-label={`Delete ${board.name}`}
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18" /><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" /><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" /></svg>
                </button>
              )}
            </div>
          )}
        </div>
      ))}

      {isCreating ? (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleCreate();
          }}
          className="flex items-center gap-1"
        >
          <input
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Board name"
            className="w-28 rounded-lg border border-[var(--stroke)] px-2 py-1 text-xs text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)]"
            autoFocus
            maxLength={100}
            onBlur={() => {
              if (!newName.trim()) setIsCreating(false);
            }}
            aria-label="New board name"
          />
          <button
            type="submit"
            className="rounded-lg bg-[var(--secondary-purple)] px-2 py-1 text-xs font-semibold text-white"
          >
            Add
          </button>
          <button
            type="button"
            onClick={() => {
              setIsCreating(false);
              setNewName("");
            }}
            className="rounded-lg border border-[var(--stroke)] px-2 py-1 text-xs text-[var(--gray-text)]"
          >
            Cancel
          </button>
        </form>
      ) : (
        <button
          type="button"
          onClick={() => setIsCreating(true)}
          className="flex items-center gap-1 rounded-lg border border-dashed border-[var(--stroke)] px-3 py-1.5 text-xs font-semibold text-[var(--gray-text)] transition hover:border-[var(--primary-blue)] hover:text-[var(--primary-blue)]"
          aria-label="Create new board"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5v14" /><path d="M5 12h14" /></svg>
          New Board
        </button>
      )}
    </div>
  );
};
