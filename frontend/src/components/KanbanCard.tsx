import { useState } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import clsx from "clsx";
import type { Card } from "@/lib/kanban";

type KanbanCardProps = {
  card: Card;
  onDelete: (cardId: string) => void;
  onUpdate: (cardId: string, title: string, details: string) => void;
};

export const KanbanCard = ({ card, onDelete, onUpdate }: KanbanCardProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [titleValue, setTitleValue] = useState(card.title);
  const [detailsValue, setDetailsValue] = useState(card.details);

  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: card.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <article
      ref={setNodeRef}
      style={style}
      className={clsx(
        "rounded-2xl border border-transparent bg-white px-3.5 py-3 shadow-[0_8px_20px_rgba(3,33,71,0.06)]",
        "transition-all duration-150",
        isDragging && "opacity-60 shadow-[0_18px_32px_rgba(3,33,71,0.16)]"
      )}
      {...(isEditing ? {} : attributes)}
      {...(isEditing ? {} : listeners)}
      data-testid={`card-${card.id}`}
    >
      <div className="flex items-start justify-between gap-2">
        {isEditing ? (
          <div className="w-full space-y-3">
            <input
              value={titleValue}
              onChange={(event) => setTitleValue(event.target.value)}
              maxLength={200}
              className="w-full rounded-xl border border-[var(--stroke)] px-3 py-2 text-sm font-semibold text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)]"
              aria-label="Card title"
            />
            <textarea
              value={detailsValue}
              onChange={(event) => setDetailsValue(event.target.value)}
              maxLength={5000}
              className="w-full resize-none rounded-xl border border-[var(--stroke)] px-3 py-2 text-sm text-[var(--gray-text)] outline-none focus:border-[var(--primary-blue)]"
              rows={3}
              aria-label="Card details"
            />
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => {
                  onUpdate(card.id, titleValue, detailsValue);
                  setIsEditing(false);
                }}
                className="rounded-full bg-[var(--secondary-purple)] px-3 py-2 text-xs font-semibold uppercase tracking-wide text-white"
              >
                Save
              </button>
              <button
                type="button"
                onClick={() => {
                  setTitleValue(card.title);
                  setDetailsValue(card.details);
                  setIsEditing(false);
                }}
                className="rounded-full border border-[var(--stroke)] px-3 py-2 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)]"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="min-w-0 flex-1">
              <h4 className="font-display text-sm font-semibold leading-snug text-[var(--navy-dark)]">
                {card.title}
              </h4>
              <p className="mt-1.5 text-xs leading-5 text-[var(--gray-text)]">
                {card.details}
              </p>
            </div>
            <div className="flex shrink-0 items-center gap-0.5">
              <button
                type="button"
                onClick={() => setIsEditing(true)}
                className="rounded-lg p-1.5 text-[var(--gray-text)] transition hover:bg-[var(--surface)] hover:text-[var(--navy-dark)]"
                aria-label={`Edit ${card.title}`}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" /><path d="m15 5 4 4" /></svg>
              </button>
              <button
                type="button"
                onClick={() => onDelete(card.id)}
                className="rounded-lg p-1.5 text-[var(--gray-text)] transition hover:bg-red-50 hover:text-red-500"
                aria-label={`Delete ${card.title}`}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18" /><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" /><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" /></svg>
              </button>
            </div>
          </>
        )}
      </div>
    </article>
  );
};
