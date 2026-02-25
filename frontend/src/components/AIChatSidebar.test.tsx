import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AIChatSidebar } from "@/components/AIChatSidebar";
import { initialData } from "@/lib/kanban";

const originalFetch = global.fetch;

describe("AIChatSidebar", () => {
  afterEach(() => {
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it("sends message and renders assistant response", async () => {
    const onBoardUpdate = vi.fn();

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        assistant_response: "You can review high-priority cards first.",
        board: initialData,
        board_updated: false,
      }),
    }) as unknown as typeof fetch;

    render(<AIChatSidebar board={initialData} onBoardUpdate={onBoardUpdate} />);

    await userEvent.type(screen.getByLabelText("AI message"), "What should I do next?");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    await waitFor(() => {
      expect(
        screen.getByText("You can review high-priority cards first.")
      ).toBeInTheDocument();
    });

    expect(onBoardUpdate).not.toHaveBeenCalled();
  });

  it("applies board update when AI returns one", async () => {
    const nextBoard = {
      ...initialData,
      cards: {
        ...initialData.cards,
        "card-1": {
          ...initialData.cards["card-1"],
          title: "Updated by AI",
        },
      },
    };

    const onBoardUpdate = vi.fn();

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        assistant_response: "Updated card 1.",
        board: nextBoard,
        board_updated: true,
      }),
    }) as unknown as typeof fetch;

    render(<AIChatSidebar board={initialData} onBoardUpdate={onBoardUpdate} />);

    await userEvent.type(screen.getByLabelText("AI message"), "Update card 1");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    await waitFor(() => {
      expect(onBoardUpdate).toHaveBeenCalledWith(nextBoard);
    });
  });
});
