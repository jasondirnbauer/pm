import { expect, test } from "@playwright/test";

const defaultBoard = {
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
      title: "Define product vision",
      details: "Draft quarterly themes with impact statements and metrics.",
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
};

const signIn = async (page: import("@playwright/test").Page) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();

  await page.request.put("/api/board", {
    data: defaultBoard,
  });
  await page.reload();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
};

test("persists edited card after reload", async ({ page }) => {
  await signIn(page);

  const marker = `persist-edit-${Date.now()}`;
  const card = page.getByTestId("card-card-1");

  await card.getByRole("button", { name: /^Edit\b/i }).click({ force: true });
  await card.getByLabel("Card title").fill(marker);
  await card.getByRole("button", { name: /save/i }).click();

  await expect(page.getByText(marker)).toBeVisible();
  await page.reload();
  await expect(page.getByText(marker)).toBeVisible();
});

test("persists moved card after reload", async ({ page }) => {
  await signIn(page);

  const card = page.getByTestId("card-card-1");
  const targetColumn = page.getByTestId("column-col-review");

  await expect(card).toBeVisible();
  await expect(targetColumn).toBeVisible();

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
  await page.reload();
  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();
});

test("applies AI updates to board without reload", async ({ page }) => {
  await signIn(page);

  const aiMarker = `ai-marker-${Date.now()}`;

  await page.route("**/api/ai/board-action", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        model: "openai/gpt-oss-120b",
        assistant_response: "Applied update.",
        board: {
          ...defaultBoard,
          cards: {
            ...defaultBoard.cards,
            "card-1": {
              ...defaultBoard.cards["card-1"],
              title: aiMarker,
            },
          },
        },
        board_updated: true,
      }),
    });
  });

  await page.getByLabel("AI message").fill("Update card title");
  await page.getByRole("button", { name: /send/i }).click();

  await expect(page.getByText("Applied update.")).toBeVisible();
  await expect(page.getByText(aiMarker)).toBeVisible();
});
