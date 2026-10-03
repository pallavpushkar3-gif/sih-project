import { expect, test } from "@playwright/test";

test("scenario run is labelled as a simulated projection", async ({ page }) => {
  await page.goto("/scenarios");
  await expect(page.getByText("Simulated projections", { exact: true })).toBeVisible();
  const submitted = page.waitForResponse(
    (response) =>
      response.url().includes("/api/jobs/simulation/") &&
      response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Queue deterministic reference" }).first().click();
  const job = (await (await submitted).json()) as { id: string };
  await expect(page.getByRole("heading", { name: "Calculation jobs" })).toBeVisible();
  const jobRow = page.getByRole("row").filter({ hasText: job.id });
  await expect(jobRow).toContainText("succeeded");
  await expect(jobRow).toContainText(`sim-for-${job.id}`);
  await expect(page.getByText("simulated projection").first()).toBeVisible();
});
