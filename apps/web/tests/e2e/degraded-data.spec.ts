import { expect, test } from "@playwright/test";

test("degraded data never displays a fabricated estimate", async ({ page }) => {
  await page.goto("/components/cmp-eng-02");
  await expect(page.getByText("Prediction is unavailable", { exact: true })).toBeVisible();
  await expect(page.getByText("No model installed", { exact: true })).toBeVisible();
  await expect(page.getByText(/No numerical life estimate is substituted/i)).toBeVisible();
});
