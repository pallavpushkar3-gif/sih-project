import { describe, expect, it } from "vitest";

import { arrayOf, isFleetItem, isSimulationRun } from "./client";

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
});
