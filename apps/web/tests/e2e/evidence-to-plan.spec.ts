import { expect, test } from "@playwright/test";

test("evidence remains honest before planning", async ({ page }) => {
  test.setTimeout(60000);
  await page.goto("/fleet/register");
  await expect(page.getByRole("heading", { name: "Fleet overview", exact: true })).toBeVisible();
  await page.getByRole("link", { name: "SYN-001", exact:true }).click();
  await expect(page.getByRole("heading",{name:"ENG-SYN-001",exact:true})).toBeVisible();
  await expect(page.getByRole("heading",{name:"Quality & applicability"})).toBeVisible();
  await page.getByRole("navigation").getByRole("link", { name: "Planning" }).click();
  await expect(page.getByRole("heading", { name: "Maintenance planning" })).toBeVisible();
  const submitted = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/jobs/planning") && response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Calculate maintenance schedule" }).click();
  const response = await submitted;
  expect(response.status(), await response.text()).toBe(200);
  const job = (await response.json()) as { id: string };
  const jobRow = page.locator(`[data-job-id="${job.id}"]`);
  await expect(jobRow).toContainText("Completed",{timeout:30000});
  await expect(jobRow).toContainText("Plan ready for review");
});
