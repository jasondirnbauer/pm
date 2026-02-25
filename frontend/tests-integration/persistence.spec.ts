import { expect, test } from "@playwright/test";

const signIn = async (page: import("@playwright/test").Page) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
};

test("persists edited card after reload", async ({ page }) => {
  await signIn(page);

  const marker = `persist-edit-${Date.now()}`;
  const card = page.getByTestId("card-card-1");

  await card.getByRole("button", { name: "Edit" }).click();
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
