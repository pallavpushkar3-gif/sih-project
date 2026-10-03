import { expect, test } from "@playwright/test";

test("degraded data never displays a fabricated estimate", async ({ page }) => {
  await page.goto("/components/cmp-eng-01");
  await expect(page.getByText("Prediction is intentionally unavailable", { exact: true })).toBeVisible();
  await expect(page.getByText("None", { exact: true })).toBeVisible();
  await expect(page.getByText(/not a guessed life estimate/i)).toBeVisible();
});
