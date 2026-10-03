import { expect, test } from "@playwright/test";

test("scenario run is labelled as a simulated projection", async ({ page }) => {
  await page.goto("/scenarios");
  await expect(page.getByText("Simulated projections", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Run deterministic reference" }).first().click();
  await expect(page.getByText("simulated projection").first()).toBeVisible();
});
