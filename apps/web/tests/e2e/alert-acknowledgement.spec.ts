import { expect, test } from "@playwright/test";

test("acknowledgement records review without resolving the alert", async ({ page }) => {
  await page.goto("/alerts");
  const alert = page.getByRole("article").filter({ hasText: "Health estimate needs technical review" });
  await expect(alert).toContainText("data unavailable");
  const review = alert.getByRole("button", { name: "Record technical review" });
  if (await review.count()) await review.click();
  await expect(alert).toContainText("demo-engineer");
  await expect(alert).toContainText("data unavailable");
});
