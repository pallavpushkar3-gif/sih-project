import { expect, test } from "@playwright/test";

test("scenario run is labelled as a simulated projection", async ({ page }) => {
  await page.goto("/scenarios");
  await expect(page.getByText("Simulated projections", { exact: true })).toBeVisible();
  const submitted = page.waitForResponse(
    (response) =>
      response.url().includes("/api/jobs/simulation/") &&
      response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Run comparison" }).first().click();
  const job = (await (await submitted).json()) as { id: string };
  await expect(page.getByRole("heading", { name: "Calculation activity" })).toBeVisible();
  const jobRow = page.locator(`[data-job-id="${job.id}"]`);
  await expect(jobRow).toContainText("succeeded");
  await expect(jobRow).toContainText("Projection saved");
  await expect(page.getByText("simulated projection").first()).toBeVisible();
});
