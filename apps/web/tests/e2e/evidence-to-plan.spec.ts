import { expect, test } from "@playwright/test";

test("evidence remains honest before planning", async ({ page }) => {
  await page.goto("/fleet");
  await expect(page.getByRole("heading", { name: "Fleet overview" })).toBeVisible();
  await page.getByRole("link", { name: "SYN-001" }).click();
  await expect(page.getByText("Assessment unavailable", { exact: true })).toBeVisible();
  await expect(page.getByText(/No evaluated model artifact/)).toBeVisible();
  await page.getByRole("link", { name: "Planning" }).click();
  await expect(page.getByRole("heading", { name: "Maintenance planning" })).toBeVisible();
});
