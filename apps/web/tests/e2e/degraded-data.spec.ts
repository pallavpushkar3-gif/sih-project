import { expect, test } from "@playwright/test";

test("degraded data never displays a fabricated estimate", async ({ page }) => {
  await page.goto("/components/cmp-eng-01");
  await expect(page.getByText("Assessment unavailable", { exact: true })).toBeVisible();
  await expect(page.getByText("Model: Not installed")).toBeVisible();
  await expect(page.getByText(/no numerical estimate is substituted/i)).toBeVisible();
});
