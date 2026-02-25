import { expect, test, type Page } from "@playwright/test";

const setupAuthApiMocks = async (page: Page) => {
  let isLoggedIn = false;

  await page.route("**/api/auth/me", async (route) => {
    if (isLoggedIn) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ username: "user" }),
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
    const payload = route.request().postDataJSON() as {
      username?: string;
      password?: string;
    };

    if (payload.username === "user" && payload.password === "password") {
      isLoggedIn = true;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ username: "user" }),
      });
      return;
    }

    await route.fulfill({
      status: 401,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Invalid username or password" }),
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
};

const signIn = async (page: Page) => {
  await setupAuthApiMocks(page);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
};

test("loads the kanban board", async ({ page }) => {
  await signIn(page);
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
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
    const response = {
      model: "openai/gpt-oss-120b",
      assistant_response: "I updated card 1.",
      board_updated: true,
      board: {
        columns: [
          { id: "col-backlog", title: "Backlog", cardIds: ["card-1", "card-2"] },
          { id: "col-discovery", title: "Discovery", cardIds: ["card-3"] },
          { id: "col-progress", title: "In Progress", cardIds: ["card-4", "card-5"] },
          { id: "col-review", title: "Review", cardIds: ["card-6"] },
          { id: "col-done", title: "Done", cardIds: ["card-7", "card-8"] },
        ],
        cards: {
          "card-1": {
            id: "card-1",
            title: "AI Updated Card",
            details: "Updated details.",
          },
          "card-2": {
            id: "card-2",
            title: "Gather customer signals",
            details: "Review support tags, sales notes, and churn feedback.",
          },
          "card-3": {
            id: "card-3",
            title: "Prototype analytics view",
            details: "Sketch initial dashboard layout and key drill-downs.",
          },
          "card-4": {
            id: "card-4",
            title: "Refine status language",
            details: "Standardize column labels and tone across the board.",
          },
          "card-5": {
            id: "card-5",
            title: "Design card layout",
            details: "Add hierarchy and spacing for scanning dense lists.",
          },
          "card-6": {
            id: "card-6",
            title: "QA micro-interactions",
            details: "Verify hover, focus, and loading states.",
          },
          "card-7": {
            id: "card-7",
            title: "Ship marketing page",
            details: "Final copy approved and asset pack delivered.",
          },
          "card-8": {
            id: "card-8",
            title: "Close onboarding sprint",
            details: "Document release notes and share internally.",
          },
        },
      },
    };

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(response),
    });
  });

  await page.getByLabel("AI message").fill("Update card 1");
  await page.getByRole("button", { name: /send/i }).click();

  await expect(page.getByText("I updated card 1.")).toBeVisible();
  await expect(page.getByText("AI Updated Card")).toBeVisible();
});
