import { useState } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import clsx from "clsx";
import type { Card, CardLabel, CardPriority } from "@/lib/kanban";
import { LABEL_COLORS, PRIORITY_CONFIG, createId } from "@/lib/kanban";

type KanbanCardProps = {
  card: Card;
  onDelete: (cardId: string) => void;
  onUpdate: (cardId: string, title: string, details: string, extra?: { labels?: CardLabel[]; due_date?: string | null; priority?: CardPriority }) => void;
};

export const KanbanCard = ({ card, onDelete, onUpdate }: KanbanCardProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [titleValue, setTitleValue] = useState(card.title);
  const [detailsValue, setDetailsValue] = useState(card.details);
  const [labels, setLabels] = useState<CardLabel[]>(card.labels ?? []);
  const [dueDate, setDueDate] = useState(card.due_date ?? "");
  const [priority, setPriority] = useState<CardPriority>(card.priority ?? "none");
  const [newLabelText, setNewLabelText] = useState("");
  const [selectedColor, setSelectedColor] = useState(LABEL_COLORS[0]);

  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: card.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const handleStartEdit = () => {
    setTitleValue(card.title);
    setDetailsValue(card.details);
    setLabels(card.labels ?? []);
    setDueDate(card.due_date ?? "");
    setPriority(card.priority ?? "none");
    setIsEditing(true);
  };

  const handleSave = () => {
    onUpdate(card.id, titleValue, detailsValue, {
      labels,
      due_date: dueDate || null,
      priority,
    });
    setIsEditing(false);
  };

  const handleCancel = () => {
    setTitleValue(card.title);
    setDetailsValue(card.details);
    setLabels(card.labels ?? []);
    setDueDate(card.due_date ?? "");
    setPriority(card.priority ?? "none");
    setIsEditing(false);
  };

  const addLabel = () => {
    const text = newLabelText.trim();
    if (!text || labels.length >= 10) return;
    setLabels([...labels, { id: createId("lbl"), text, color: selectedColor }]);
    setNewLabelText("");
  };

  const removeLabel = (labelId: string) => {
    setLabels(labels.filter((l) => l.id !== labelId));
  };

  const priorityColor = card.priority && card.priority !== "none"
    ? PRIORITY_CONFIG[card.priority].color
    : null;

  const isOverdue = card.due_date && new Date(card.due_date) < new Date(new Date().toISOString().slice(0, 10));
  const isDueToday = card.due_date === new Date().toISOString().slice(0, 10);

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

            {/* Priority */}
            <div>
              <span className="block text-[10px] font-semibold uppercase tracking-[0.15em] text-[var(--gray-text)] mb-1">Priority</span>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as CardPriority)}
                className="w-full rounded-xl border border-[var(--stroke)] px-3 py-2 text-sm text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)]"
                aria-label="Card priority"
              >
                {(Object.keys(PRIORITY_CONFIG) as CardPriority[]).map((p) => (
                  <option key={p} value={p}>{PRIORITY_CONFIG[p].label}</option>
                ))}
              </select>
            </div>

            {/* Due Date */}
            <div>
              <span className="block text-[10px] font-semibold uppercase tracking-[0.15em] text-[var(--gray-text)] mb-1">Due Date</span>
              <input
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                className="w-full rounded-xl border border-[var(--stroke)] px-3 py-2 text-sm text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)]"
                aria-label="Card due date"
              />
            </div>

            {/* Labels */}
            <div>
              <span className="block text-[10px] font-semibold uppercase tracking-[0.15em] text-[var(--gray-text)] mb-1">Labels</span>
              <div className="flex flex-wrap gap-1 mb-2">
                {labels.map((label) => (
                  <span
                    key={label.id}
                    className="flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold text-white"
                    style={{ backgroundColor: label.color }}
                  >
                    {label.text}
                    <button
                      type="button"
                      onClick={() => removeLabel(label.id)}
                      className="ml-0.5 opacity-80 hover:opacity-100"
                      aria-label={`Remove label ${label.text}`}
                    >
                      x
                    </button>
                  </span>
                ))}
              </div>
              <div className="flex items-center gap-1">
                <input
                  value={newLabelText}
                  onChange={(e) => setNewLabelText(e.target.value)}
                  placeholder="Label text"
                  maxLength={30}
                  className="flex-1 rounded-lg border border-[var(--stroke)] px-2 py-1 text-xs text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)]"
                  aria-label="New label text"
                />
                <div className="flex gap-0.5">
                  {LABEL_COLORS.map((color) => (
                    <button
                      key={color}
                      type="button"
                      onClick={() => setSelectedColor(color)}
                      className={clsx(
                        "h-4 w-4 rounded-full border-2 transition",
                        selectedColor === color ? "border-[var(--navy-dark)]" : "border-transparent"
                      )}
                      style={{ backgroundColor: color }}
                      aria-label={`Color ${color}`}
                    />
                  ))}
                </div>
                <button
                  type="button"
                  onClick={addLabel}
                  className="rounded-lg bg-[var(--surface)] px-2 py-1 text-[10px] font-semibold text-[var(--navy-dark)]"
                >
                  Add
                </button>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleSave}
                className="rounded-full bg-[var(--secondary-purple)] px-3 py-2 text-xs font-semibold uppercase tracking-wide text-white"
              >
                Save
              </button>
              <button
                type="button"
                onClick={handleCancel}
                className="rounded-full border border-[var(--stroke)] px-3 py-2 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)]"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-1.5">
                {priorityColor && (
                  <span
                    className="h-2 w-2 shrink-0 rounded-full"
                    style={{ backgroundColor: priorityColor }}
                    title={`Priority: ${PRIORITY_CONFIG[card.priority!].label}`}
                  />
                )}
                <h4 className="font-display text-sm font-semibold leading-snug text-[var(--navy-dark)]">
                  {card.title}
                </h4>
              </div>
              <p className="mt-1.5 text-xs leading-5 text-[var(--gray-text)]">
                {card.details}
              </p>

              {/* Labels display */}
              {card.labels && card.labels.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {card.labels.map((label) => (
                    <span
                      key={label.id}
                      className="rounded-full px-2 py-0.5 text-[10px] font-semibold text-white"
                      style={{ backgroundColor: label.color }}
                    >
                      {label.text}
                    </span>
                  ))}
                </div>
              )}

              {/* Due date display */}
              {card.due_date && (
                <p className={clsx(
                  "mt-1.5 text-[10px] font-semibold",
                  isOverdue && "text-red-500",
                  isDueToday && "text-[var(--accent-yellow)]",
                  !isOverdue && !isDueToday && "text-[var(--gray-text)]"
                )}>
                  Due: {card.due_date}
                </p>
              )}
            </div>
            <div className="flex shrink-0 items-center gap-0.5">
              <button
                type="button"
                onClick={handleStartEdit}
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
