"use client";

import { FormEvent, useState } from "react";
import type { BoardData } from "@/lib/kanban";

type ChatRole = "user" | "assistant";

type ChatMessage = {
  role: ChatRole;
  content: string;
};

type AIChatSidebarProps = {
  board: BoardData;
  onBoardUpdate: (nextBoard: BoardData) => void;
};

type AIBoardActionResponse = {
  assistant_response: string;
  board: BoardData;
  board_updated: boolean;
};

export const AIChatSidebar = ({ board, onBoardUpdate }: AIChatSidebarProps) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [prompt, setPrompt] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const question = prompt.trim();
    if (!question || isSending) {
      return;
    }

    const userMessage: ChatMessage = { role: "user", content: question };
    const nextMessages = [...messages, userMessage];

    setMessages(nextMessages);
    setPrompt("");
    setError(null);
    setIsSending(true);

    try {
      const response = await fetch("/api/ai/board-action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({
          question,
          conversation_history: messages.map((message) => ({
            role: message.role,
            content: message.content,
          })),
          board,
        }),
      });

      if (!response.ok) {
        if (response.status === 401) {
          setError("Session expired. Please log in again.");
        } else {
          const detail = await response.text();
          setError(detail || "AI request failed.");
        }
        return;
      }

      const payload = (await response.json()) as AIBoardActionResponse;
      if (typeof payload.assistant_response !== "string") {
        setError("Unexpected response from AI. Please try again.");
        return;
      }

      setMessages((current) => [
        ...current,
        { role: "assistant", content: payload.assistant_response },
      ]);

      if (payload.board_updated) {
        onBoardUpdate(payload.board);
      }
    } catch {
      setError("Unable to connect. Please check your connection and try again.");
    } finally {
      setIsSending(false);
    }
  };

  return (
    <aside className="flex h-full flex-col rounded-3xl border border-[var(--stroke)] bg-white/90 p-4 shadow-[var(--shadow)] backdrop-blur">
      <h2 className="font-display text-lg font-semibold text-[var(--navy-dark)]">
        AI Assistant
      </h2>
      <p className="mt-2 text-sm text-[var(--gray-text)]">
        Ask for suggestions or board edits. Changes apply automatically when returned.
      </p>

      <div className="mt-4 flex-1 space-y-3 overflow-auto rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] p-3">
        {messages.length === 0 ? (
          <p className="text-sm text-[var(--gray-text)]">
            Try: "Move a card from Backlog to Review and explain why."
          </p>
        ) : (
          messages.map((message, index) => (
            <div
              key={`${message.role}-${index}`}
              className={`rounded-xl px-3 py-2 text-sm ${
                message.role === "user"
                  ? "bg-[var(--primary-blue)] text-white"
                  : "border border-[var(--stroke)] bg-white text-[var(--navy-dark)]"
              }`}
            >
              <p className="font-semibold uppercase tracking-wide text-[10px] opacity-80">
                {message.role}
              </p>
              <p className="mt-1 whitespace-pre-wrap">{message.content}</p>
            </div>
          ))
        )}
      </div>

      <form onSubmit={handleSubmit} className="mt-4 space-y-3">
        <textarea
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          placeholder="Ask the assistant..."
          rows={4}
          className="w-full resize-none rounded-xl border border-[var(--stroke)] px-3 py-2 text-sm text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)]"
          aria-label="AI message"
        />
        {error ? <p className="text-sm text-[var(--secondary-purple)]">{error}</p> : null}
        <button
          type="submit"
          disabled={isSending}
          className="w-full rounded-full bg-[var(--secondary-purple)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.15em] text-white transition hover:brightness-110 disabled:opacity-60"
        >
          {isSending ? "Sending..." : "Send"}
        </button>
      </form>
    </aside>
  );
};
