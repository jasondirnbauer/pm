import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthGate } from "@/components/AuthGate";

const originalFetch = global.fetch;

describe("AuthGate", () => {
  afterEach(() => {
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it("shows sign-in form when no session exists", async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false }) as unknown as typeof fetch;

    render(<AuthGate />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /sign in/i })).toBeInTheDocument();
    });
  });

  it("signs in and renders the kanban board", async () => {
    global.fetch = vi
      .fn()
      .mockResolvedValueOnce({ ok: false })
      .mockResolvedValueOnce({ ok: true }) as unknown as typeof fetch;

    render(<AuthGate />);

    await screen.findByRole("heading", { name: /sign in/i });
    await userEvent.clear(screen.getByLabelText(/username/i));
    await userEvent.type(screen.getByLabelText(/username/i), "user");
    await userEvent.clear(screen.getByLabelText(/password/i));
    await userEvent.type(screen.getByLabelText(/password/i), "password");

    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /kanban studio/i })
      ).toBeInTheDocument();
    });
  });

  it("shows an error for invalid credentials", async () => {
    global.fetch = vi
      .fn()
      .mockResolvedValueOnce({ ok: false })
      .mockResolvedValueOnce({ ok: false }) as unknown as typeof fetch;

    render(<AuthGate />);

    await screen.findByRole("heading", { name: /sign in/i });
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/invalid username or password/i)
      ).toBeInTheDocument();
    });
  });
});
