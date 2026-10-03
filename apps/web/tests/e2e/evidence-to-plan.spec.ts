import { expect, test } from "@playwright/test";

test("evidence remains honest before planning", async ({ page }) => {
  await page.goto("/fleet");
  await expect(page.getByRole("heading", { name: /Keep every aircraft ready/ })).toBeVisible();
  await page.getByRole("link", { name: "SYN-001" }).click();
  await expect(page.getByText("Prediction is intentionally unavailable", { exact: true })).toBeVisible();
  await expect(page.getByText(/validated model has not been approved/)).toBeVisible();
  await page.getByRole("link", { name: "Work plan", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Maintenance planning" })).toBeVisible();
  const submitted = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/jobs/planning") && response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Queue proposal calculation" }).click();
  const job = (await (await submitted).json()) as { id: string };
  const jobRow = page.locator(`[data-job-id="${job.id}"]`);
  await expect(jobRow).toContainText("succeeded");
  await expect(jobRow).toContainText("Plan ready for review");
});
