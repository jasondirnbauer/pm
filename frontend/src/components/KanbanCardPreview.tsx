import type { Card } from "@/lib/kanban";
import { PRIORITY_CONFIG } from "@/lib/kanban";

type KanbanCardPreviewProps = {
  card: Card;
};

export const KanbanCardPreview = ({ card }: KanbanCardPreviewProps) => {
  const priorityColor = card.priority && card.priority !== "none"
    ? PRIORITY_CONFIG[card.priority].color
    : null;

  return (
    <article className="rounded-2xl border border-transparent bg-white px-3.5 py-3 shadow-[0_18px_32px_rgba(3,33,71,0.16)]">
      <div className="flex items-center gap-1.5">
        {priorityColor && (
          <span
            className="h-2 w-2 shrink-0 rounded-full"
            style={{ backgroundColor: priorityColor }}
          />
        )}
        <h4 className="font-display text-sm font-semibold leading-snug text-[var(--navy-dark)]">
          {card.title}
        </h4>
      </div>
      <p className="mt-1.5 text-xs leading-5 text-[var(--gray-text)]">
        {card.details}
      </p>
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
    </article>
  );
};
