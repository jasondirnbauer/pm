import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BoardSelector } from "@/components/BoardSelector";
import type { BoardSummary } from "@/lib/kanban";

const boards: BoardSummary[] = [
  { id: "board-1", name: "Sprint 1", created_at: "2026-01-01", updated_at: "2026-01-01" },
  { id: "board-2", name: "Sprint 2", created_at: "2026-02-01", updated_at: "2026-02-01" },
];

describe("BoardSelector", () => {
  it("renders board tabs", () => {
    render(
      <BoardSelector
        boards={boards}
        activeBoardId="board-1"
        onSelectBoard={vi.fn()}
        onCreateBoard={vi.fn()}
        onRenameBoard={vi.fn()}
        onDeleteBoard={vi.fn()}
      />
    );

    expect(screen.getByText("Sprint 1")).toBeInTheDocument();
    expect(screen.getByText("Sprint 2")).toBeInTheDocument();
  });

  it("selects a board when clicked", async () => {
    const onSelect = vi.fn();
    render(
      <BoardSelector
        boards={boards}
        activeBoardId="board-1"
        onSelectBoard={onSelect}
        onCreateBoard={vi.fn()}
        onRenameBoard={vi.fn()}
        onDeleteBoard={vi.fn()}
      />
    );

    await userEvent.click(screen.getByText("Sprint 2"));
    expect(onSelect).toHaveBeenCalledWith("board-2");
  });

  it("creates a new board", async () => {
    const onCreate = vi.fn();
    render(
      <BoardSelector
        boards={boards}
        activeBoardId="board-1"
        onSelectBoard={vi.fn()}
        onCreateBoard={onCreate}
        onRenameBoard={vi.fn()}
        onDeleteBoard={vi.fn()}
      />
    );

    await userEvent.click(screen.getByLabelText("Create new board"));
    await userEvent.type(screen.getByLabelText("New board name"), "Sprint 3");
    await userEvent.click(screen.getByText("Add"));

    expect(onCreate).toHaveBeenCalledWith("Sprint 3");
  });

  it("shows rename and delete on active board hover", async () => {
    render(
      <BoardSelector
        boards={boards}
        activeBoardId="board-1"
        onSelectBoard={vi.fn()}
        onCreateBoard={vi.fn()}
        onRenameBoard={vi.fn()}
        onDeleteBoard={vi.fn()}
      />
    );

    // The rename/delete buttons exist for the active board
    expect(screen.getByLabelText("Rename Sprint 1")).toBeInTheDocument();
    expect(screen.getByLabelText("Delete Sprint 1")).toBeInTheDocument();
  });
});
