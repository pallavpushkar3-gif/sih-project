import { expect, test } from "@playwright/test";

test("evidence remains honest before planning", async ({ page }) => {
  await page.goto("/fleet");
  await expect(page.getByRole("heading", { name: "Fleet overview" })).toBeVisible();
  await page.getByRole("link", { name: "SYN-001" }).click();
  await expect(page.getByText("Assessment unavailable", { exact: true })).toBeVisible();
  await expect(page.getByText(/No evaluated model artifact/)).toBeVisible();
  await page.getByRole("link", { name: "Planning" }).click();
  await expect(page.getByRole("heading", { name: "Maintenance planning" })).toBeVisible();
  const submitted = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/jobs/planning") && response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Queue proposal calculation" }).click();
  const job = (await (await submitted).json()) as { id: string };
  const jobRow = page.getByRole("row").filter({ hasText: job.id });
  await expect(jobRow).toContainText("succeeded");
  await expect(jobRow).toContainText(`plan-for-${job.id}`);
});
