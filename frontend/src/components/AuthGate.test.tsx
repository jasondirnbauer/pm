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
      // authMe check
      .mockResolvedValueOnce({ ok: false })
      // authLogin
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ username: "user", display_name: "Default User" }),
      }) as unknown as typeof fetch;

    render(<AuthGate />);

    await screen.findByRole("heading", { name: /sign in/i });
    await userEvent.clear(screen.getByLabelText(/username/i));
    await userEvent.type(screen.getByLabelText(/username/i), "user");
    await userEvent.clear(screen.getByLabelText(/password/i));
    await userEvent.type(screen.getByLabelText(/password/i), "password");

    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/log out/i)).toBeInTheDocument();
    });
  });

  it("shows an error for invalid credentials", async () => {
    global.fetch = vi
      .fn()
      // authMe check
      .mockResolvedValueOnce({ ok: false })
      // authLogin fail
      .mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: "Invalid username or password" }),
      }) as unknown as typeof fetch;

    render(<AuthGate />);

    await screen.findByRole("heading", { name: /sign in/i });
    await userEvent.type(screen.getByLabelText(/username/i), "baduser");
    await userEvent.type(screen.getByLabelText(/password/i), "badpass");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/invalid username or password/i)
      ).toBeInTheDocument();
    });
  });

  it("shows registration form when toggled", async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false }) as unknown as typeof fetch;

    render(<AuthGate />);

    await screen.findByRole("heading", { name: /sign in/i });
    await userEvent.click(screen.getByText(/create one/i));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /create account/i })).toBeInTheDocument();
      expect(screen.getByLabelText(/display name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    });
  });

  it("registers and auto-logs in", async () => {
    global.fetch = vi
      .fn()
      // authMe check
      .mockResolvedValueOnce({ ok: false })
      // authRegister
      .mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => ({ username: "newuser", display_name: "New User" }),
      }) as unknown as typeof fetch;

    render(<AuthGate />);

    await screen.findByRole("heading", { name: /sign in/i });
    await userEvent.click(screen.getByText(/create one/i));

    await userEvent.type(screen.getByLabelText(/username/i), "newuser");
    await userEvent.type(screen.getByLabelText(/^password$/i), "secret123");
    await userEvent.type(screen.getByLabelText(/confirm password/i), "secret123");

    await userEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText(/log out/i)).toBeInTheDocument();
    });
  });

  it("shows error when passwords do not match", async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false }) as unknown as typeof fetch;

    render(<AuthGate />);

    await screen.findByRole("heading", { name: /sign in/i });
    await userEvent.click(screen.getByText(/create one/i));

    await userEvent.type(screen.getByLabelText(/username/i), "newuser");
    await userEvent.type(screen.getByLabelText(/^password$/i), "secret123");
    await userEvent.type(screen.getByLabelText(/confirm password/i), "different");

    await userEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
    });
  });
});
