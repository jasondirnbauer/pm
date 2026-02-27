"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  pointerWithin,
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  type CollisionDetection,
  closestCorners,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { AIChatSidebar } from "@/components/AIChatSidebar";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import { createId, initialData, moveCard, type BoardData } from "@/lib/kanban";

const shouldUseBackendPersistence = process.env.NODE_ENV !== "test";

// Debounce rapid edits so only the final state within this window is persisted
const PERSIST_DEBOUNCE_MS = 300;
// Abort stalled persistence requests after this timeout
const PERSIST_TIMEOUT_MS = 10_000;

const COLUMN_COLORS = ["#209dd7", "#ecad0a", "#753991", "#22c55e", "#f97316"];

export const KanbanBoard = () => {
  const [board, setBoard] = useState<BoardData>(() => initialData);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [loadError, setLoadError] = useState(false);

  // Mirrors board state so applyBoardUpdate can compute the next state
  // synchronously without relying on the React state updater pattern.
  const boardRef = useRef<BoardData>(initialData);
  const persistTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    })
  );

  const collisionDetection: CollisionDetection = (args) => {
    const pointerCollisions = pointerWithin(args);
    if (pointerCollisions.length > 0) {
      const pointerY = args.pointerCoordinates?.y;
      const cardCollisions = pointerCollisions.filter((collision) =>
        String(collision.id).startsWith("card-")
      );

      if (pointerY !== undefined && cardCollisions.length > 0) {
        return [...cardCollisions].sort((left, right) => {
          const leftRect = args.droppableRects.get(left.id);
          const rightRect = args.droppableRects.get(right.id);

          if (!leftRect || !rightRect) {
            return 0;
          }

          const leftCenterY = (leftRect.top + leftRect.bottom) / 2;
          const rightCenterY = (rightRect.top + rightRect.bottom) / 2;

          return Math.abs(leftCenterY - pointerY) - Math.abs(rightCenterY - pointerY);
        });
      }

      return pointerCollisions;
    }
    return closestCorners(args);
  };

  const cardsById = useMemo(() => board.cards, [board.cards]);

  const persistBoard = async (nextBoard: BoardData) => {
    if (!shouldUseBackendPersistence) {
      return;
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), PERSIST_TIMEOUT_MS);
    try {
      await fetch("/api/board", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "same-origin",
        body: JSON.stringify(nextBoard),
        signal: controller.signal,
      });
    } finally {
      clearTimeout(timeout);
    }
  };

  const schedulePersist = (nextBoard: BoardData) => {
    if (persistTimerRef.current !== null) {
      clearTimeout(persistTimerRef.current);
    }
    persistTimerRef.current = setTimeout(() => {
      void persistBoard(nextBoard);
    }, PERSIST_DEBOUNCE_MS);
  };

  // Applies an update to the board state and keeps boardRef in sync.
  // Pass { debounce: true } for high-frequency updates (e.g. typing a column
  // rename) so rapid changes are coalesced. All other updates persist
  // immediately to ensure changes survive a page reload.
  const applyBoardUpdate = (
    updater: (current: BoardData) => BoardData,
    options: { debounce?: boolean } = {}
  ) => {
    const nextBoard = updater(boardRef.current);
    boardRef.current = nextBoard;
    setBoard(nextBoard);
    if (options.debounce) {
      schedulePersist(nextBoard);
    } else {
      if (persistTimerRef.current !== null) {
        clearTimeout(persistTimerRef.current);
        persistTimerRef.current = null;
      }
      void persistBoard(nextBoard);
    }
  };

  useEffect(() => {
    if (!shouldUseBackendPersistence) {
      return;
    }

    const loadBoard = async () => {
      try {
        const response = await fetch("/api/board", {
          method: "GET",
          credentials: "same-origin",
        });

        if (!response.ok) {
          setLoadError(true);
          return;
        }

        const payload = (await response.json()) as BoardData;
        boardRef.current = payload;
        setBoard(payload);
      } catch {
        setLoadError(true);
      }
    };

    void loadBoard();
  }, []);

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);

    if (!over || active.id === over.id) {
      return;
    }

    applyBoardUpdate((prev) => ({
      ...prev,
      columns: moveCard(prev.columns, active.id as string, over.id as string),
    }));
  };

  const handleRenameColumn = (columnId: string, title: string) => {
    applyBoardUpdate((prev) => ({
      ...prev,
      columns: prev.columns.map((column) =>
        column.id === columnId ? { ...column, title } : column
      ),
    }), { debounce: true });
  };

  const handleAddCard = (columnId: string, title: string, details: string) => {
    const id = createId("card");
    applyBoardUpdate((prev) => ({
      ...prev,
      cards: {
        ...prev.cards,
        [id]: { id, title, details: details || "No details yet." },
      },
      columns: prev.columns.map((column) =>
        column.id === columnId
          ? { ...column, cardIds: [...column.cardIds, id] }
          : column
      ),
    }));
  };

  const handleDeleteCard = (columnId: string, cardId: string) => {
    applyBoardUpdate((prev) => {
      return {
        ...prev,
        cards: Object.fromEntries(
          Object.entries(prev.cards).filter(([id]) => id !== cardId)
        ),
        columns: prev.columns.map((column) =>
          column.id === columnId
            ? {
                ...column,
                cardIds: column.cardIds.filter((id) => id !== cardId),
              }
            : column
        ),
      };
    });
  };

  const handleUpdateCard = (cardId: string, title: string, details: string) => {
    applyBoardUpdate((prev) => ({
      ...prev,
      cards: {
        ...prev.cards,
        [cardId]: {
          ...prev.cards[cardId],
          title: title.trim() || prev.cards[cardId].title,
          details: details.trim() || "No details yet.",
        },
      },
    }));
  };

  const activeCard = activeCardId ? cardsById[activeCardId] : null;

  const handleBoardUpdateFromAI = (nextBoard: BoardData) => {
    // The backend already persisted this board — just sync local state.
    boardRef.current = nextBoard;
    setBoard(nextBoard);
  };

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <main className="relative mx-auto flex min-h-screen max-w-[1920px] flex-col gap-6 px-8 pb-12 pt-8">
        {loadError && (
          <div className="rounded-xl border border-[var(--secondary-purple)] bg-white/80 px-4 py-2 text-sm text-[var(--secondary-purple)]">
            Could not load latest board — showing cached data. Refresh to try again.
          </div>
        )}

        <header className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-[var(--stroke)] bg-white/80 px-6 py-4 shadow-[var(--shadow)] backdrop-blur">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.3em] text-[var(--gray-text)]">
              Single Board Kanban
            </p>
            <h1 className="font-display text-2xl font-semibold text-[var(--navy-dark)]">
              Kanban Studio
            </h1>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            {board.columns.map((column, index) => (
              <span
                key={column.id}
                className="flex items-center gap-1.5 text-xs font-medium text-[var(--gray-text)]"
              >
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: COLUMN_COLORS[index % COLUMN_COLORS.length] }}
                />
                <span className="text-[var(--navy-dark)]">{column.title}</span>
                <span className="text-[10px]">{column.cardIds.length}</span>
              </span>
            ))}
          </div>
        </header>

        <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_320px]">
          <DndContext
            sensors={sensors}
            collisionDetection={collisionDetection}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
          >
            <div className="min-w-0 overflow-x-auto pb-2">
              <section className="grid grid-cols-[repeat(5,minmax(200px,1fr))] gap-4">
                {board.columns.map((column, index) => (
                  <KanbanColumn
                    key={column.id}
                    column={column}
                    cards={column.cardIds.map((cardId) => board.cards[cardId])}
                    accentColor={COLUMN_COLORS[index % COLUMN_COLORS.length]}
                    onRename={handleRenameColumn}
                    onAddCard={handleAddCard}
                    onDeleteCard={handleDeleteCard}
                    onUpdateCard={handleUpdateCard}
                  />
                ))}
              </section>
            </div>
            <DragOverlay>
              {activeCard ? (
                <div className="w-[240px]">
                  <KanbanCardPreview card={activeCard} />
                </div>
              ) : null}
            </DragOverlay>
          </DndContext>

          <AIChatSidebar board={board} onBoardUpdate={handleBoardUpdateFromAI} />
        </div>
      </main>
    </div>
  );
};
