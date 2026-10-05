import { afterEach, describe, expect, it, vi } from "vitest";

import { api, ApiError, arrayOf, isComponentDetail, isFleetItem, isHealth, isInventoryPart, isJob, isSimulationRun } from "./client";

describe("rate-limited API requests", () => {
  afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks(); });

  it.each([
    ["60", 60],
    ["Mon, 05 Oct 2026 08:00:45 GMT", 45],
    ["invalid", 30],
    [null, 30],
  ])("handles Retry-After %s without automatically resubmitting credentials", async (header, seconds) => {
    vi.spyOn(Date, "now").mockReturnValue(Date.parse("2026-10-05T08:00:00Z"));
    const fetch = vi.fn().mockResolvedValue(new Response("<html>Too Many Requests</html>", {
      status: 429, headers: header ? { "Retry-After": header } : {},
    }));
    vi.stubGlobal("fetch", fetch);
    const error = await api("/access/session", { method: "POST", body: "{}" }).catch((cause: unknown) => cause);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 429, retryAfterSeconds: seconds });
    expect((error as ApiError).message).toContain("Please wait");
    expect(fetch).toHaveBeenCalledTimes(1);
  });
});

describe("API runtime validators", () => {
  it("accepts a valid fleet collection", () => {
    const payload: unknown = [
      {
        id: "ac-1",
        tail_number: "SYN-001",
        label: "Synthetic aircraft",
        provenance: "synthetic",
        component_ids: ["cmp-1"],
        components: 1,
        open_tasks: 2,
      },
    ];
    expect(arrayOf(isFleetItem)(payload)).toBe(true);
  });

  it("rejects a plausible-looking response with invalid numeric data", () => {
    const payload: unknown = {
      id: "run-1",
      scenario_id: "scenario-1",
      policy: "configured",
      seed: 26249,
      availability: Number.NaN,
      metrics: {},
    };
    expect(isSimulationRun(payload)).toBe(false);
  });

  it("validates authoritative job states and attempts", () => {
    expect(
      isJob({ id: "job-1", kind: "planning", state: "queued", attempt: 0, result: null }),
    ).toBe(true);
    expect(
      isJob({ id: "job-2", kind: "planning", state: "running", attempt: -1, result: null }),
    ).toBe(false);
    expect(isJob({ id: "job-3", kind: "planning", state: "invented", attempt: 0, result: null })).toBe(false);
  });

  it("rejects impossible inventory quantities rather than showing negative free stock", () => {
    expect(isInventoryPart({ id:"kit", name:"kit", on_hand:1, reserved:2, lead_time_slots:2, version:1, provenance:"synthetic" })).toBe(false);
  });

  it("requires the actual readiness response to show a connected API", () => {
    expect(isHealth({ status:"ready", database:"ok" })).toBe(true);
    expect(isHealth({ status:"unavailable", database:"failed" })).toBe(false);
  });

  it("rejects nonnumeric assessment values before the evidence card formats them", () => {
    expect(isComponentDetail({ id:"cmp", aircraft_id:"ac", serial_number:"eng", kind:"engine", status:"monitoring", current_cycle:30, observations:[], assessment:{ id:"asm", state:"eligible", estimate_cycles:"NaN", lower_cycles:1, upper_cycles:20, model_version:"v1", input_version:"i1", quality_findings:[] } })).toBe(false);
  });
});
