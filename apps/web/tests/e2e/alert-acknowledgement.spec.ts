import { expect, test } from "@playwright/test";

test("acknowledgement records review without resolving the alert", async ({ page }) => {
  await page.goto("/alerts");
  const row = page.getByRole("row").filter({ hasText: "cmp-eng-01" });
  await expect(row).toContainText("data unavailable");
  await row.getByRole("button", { name: "Record technical review" }).click();
  await expect(row).toContainText("demo-engineer");
  await expect(row).toContainText("data unavailable");
});
