import { expect, test, type Page } from "@playwright/test";

const defaultBoard = {
  columns: [
    { id: "col-backlog", title: "Backlog", cardIds: ["card-1", "card-2"] },
    { id: "col-discovery", title: "Discovery", cardIds: ["card-3"] },
    { id: "col-progress", title: "In Progress", cardIds: ["card-4", "card-5"] },
    { id: "col-review", title: "Review", cardIds: ["card-6"] },
    { id: "col-done", title: "Done", cardIds: ["card-7", "card-8"] },
  ],
  cards: {
    "card-1": { id: "card-1", title: "Align roadmap themes", details: "Draft quarterly themes with impact statements and metrics." },
    "card-2": { id: "card-2", title: "Gather customer signals", details: "Review support tags, sales notes, and churn feedback." },
    "card-3": { id: "card-3", title: "Prototype analytics view", details: "Sketch initial dashboard layout and key drill-downs." },
    "card-4": { id: "card-4", title: "Refine status language", details: "Standardize column labels and tone across the board." },
    "card-5": { id: "card-5", title: "Design card layout", details: "Add hierarchy and spacing for scanning dense lists." },
    "card-6": { id: "card-6", title: "QA micro-interactions", details: "Verify hover, focus, and loading states." },
    "card-7": { id: "card-7", title: "Ship marketing page", details: "Final copy approved and asset pack delivered." },
    "card-8": { id: "card-8", title: "Close onboarding sprint", details: "Document release notes and share internally." },
  },
};

const setupApiMocks = async (page: Page) => {
  let isLoggedIn = false;

  await page.route("**/api/auth/me", async (route) => {
    if (isLoggedIn) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ username: "user", display_name: "Default User" }),
      });
      return;
    }
    await route.fulfill({
      status: 401,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Not authenticated" }),
    });
  });

  await page.route("**/api/auth/login", async (route) => {
    const payload = route.request().postDataJSON() as { username?: string; password?: string };
    if (payload.username === "user" && payload.password === "password") {
      isLoggedIn = true;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ username: "user", display_name: "Default User" }),
      });
      return;
    }
    await route.fulfill({
      status: 401,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Invalid username or password" }),
    });
  });

  await page.route("**/api/auth/register", async (route) => {
    const payload = route.request().postDataJSON() as { username?: string; password?: string; display_name?: string };
    isLoggedIn = true;
    await route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify({ username: payload.username, display_name: payload.display_name || "" }),
    });
  });

  await page.route("**/api/auth/logout", async (route) => {
    isLoggedIn = false;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ status: "ok" }),
    });
  });

  await page.route("**/api/boards", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          { id: "board-1", name: "My Board", created_at: "2026-01-01", updated_at: "2026-01-01" },
        ]),
      });
    } else if (route.request().method() === "POST") {
      const payload = route.request().postDataJSON() as { name: string };
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({
          id: "board-new",
          name: payload.name,
          board_json: defaultBoard,
          created_at: "2026-02-01",
          updated_at: "2026-02-01",
        }),
      });
    } else {
      await route.continue();
    }
  });

  await page.route("**/api/boards/*", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "board-1",
          name: "My Board",
          board_json: defaultBoard,
          created_at: "2026-01-01",
          updated_at: "2026-01-01",
        }),
      });
    } else if (route.request().method() === "PUT") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "board-1",
          name: "My Board",
          board_json: route.request().postDataJSON(),
          created_at: "2026-01-01",
          updated_at: "2026-01-01",
        }),
      });
    } else if (route.request().method() === "PATCH") {
      const payload = route.request().postDataJSON() as { name: string };
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "board-1",
          name: payload.name,
          created_at: "2026-01-01",
          updated_at: "2026-01-01",
        }),
      });
    } else if (route.request().method() === "DELETE") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ status: "ok" }),
      });
    } else {
      await route.continue();
    }
  });
};

const signIn = async (page: Page) => {
  await setupApiMocks(page);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page.locator('[data-testid^="column-"]').first()).toBeVisible();
};

test("loads the kanban board", async ({ page }) => {
  await signIn(page);
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("adds a card to a column", async ({ page }) => {
  await signIn(page);
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();
});

test("moves a card between columns", async ({ page }) => {
  await signIn(page);
  const card = page.getByTestId("card-card-1");
  const targetColumn = page.getByTestId("column-col-review");
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    columnBox.x + columnBox.width / 2,
    columnBox.y + 120,
    { steps: 12 }
  );
  await page.mouse.up();
  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();
});

test("logs out back to sign in", async ({ page }) => {
  await signIn(page);
  await page.getByRole("button", { name: /log out/i }).click();
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
});

test("applies AI board updates automatically", async ({ page }) => {
  await signIn(page);

  await page.route("**/api/ai/board-action", async (route) => {
    const updatedBoard = { ...defaultBoard };
    updatedBoard.cards = {
      ...defaultBoard.cards,
      "card-1": { id: "card-1", title: "AI Updated Card", details: "Updated details." },
    };

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        model: "openai/gpt-oss-120b",
        assistant_response: "I updated card 1.",
        board_updated: true,
        board: updatedBoard,
      }),
    });
  });

  await page.getByLabel("AI message").fill("Update card 1");
  await page.getByRole("button", { name: /send/i }).click();

  await expect(page.getByText("I updated card 1.")).toBeVisible();
  await expect(page.getByText("AI Updated Card")).toBeVisible();
});

test("shows registration form and registers", async ({ page }) => {
  await setupApiMocks(page);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();

  await page.getByText("Create one").click();
  await expect(page.getByRole("heading", { name: "Create account" })).toBeVisible();

  await page.getByLabel("Username").fill("newuser");
  await page.getByLabel("Display Name").fill("New User");
  await page.getByLabel("Password", { exact: true }).fill("secret123");
  await page.getByLabel("Confirm Password").fill("secret123");

  await page.getByRole("button", { name: /create account/i }).click();
  await expect(page.locator('[data-testid^="column-"]').first()).toBeVisible();
});

test("shows board selector with New Board button", async ({ page }) => {
  await signIn(page);
  await expect(page.getByText("My Board")).toBeVisible();
  await expect(page.getByLabel("Create new board")).toBeVisible();
});
