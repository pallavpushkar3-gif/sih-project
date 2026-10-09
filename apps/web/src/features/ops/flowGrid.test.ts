import { describe, expect, it } from "vitest";
import { gridMesh, warpGrid } from "./elasticGridMath";

describe("decorative flexible grid", () => {
  it("has a bounded dip and finite grid coordinates", () => {
    const well = { x: .5, y: .5, strength: 1.3, radius: .24 };
    expect(warpGrid(.5, .5, [well], []).y).toBeGreaterThan(.5);
    expect(warpGrid(.8, .5, [well], []).x).toBeLessThan(.8);
    for (let i = 0; i <= 20; i++) for (let j = 0; j <= 20; j++) {
      const result = warpGrid(i / 20, j / 20, [well], [{ x: .3, y: .6, age: .7 }]);
      expect(Number.isFinite(result.x) && Number.isFinite(result.y)).toBe(true);
      expect(Math.abs(result.y - j / 20)).toBeLessThan(.15);
    }
    expect(gridMesh()).toHaveLength(50);
    expect(gridMesh(true).length).toBeLessThan(gridMesh().length);
    expect(gridMesh().every(line => [...line].every(Number.isFinite))).toBe(true);
  });
  it("expires ripples and responds to moving wells", () => {
    expect(warpGrid(.4, .6, [], [{ x: .4, y: .6, age: 3 }])).toEqual({ x: .4, y: .6 });
    const left = warpGrid(.5, .5, [{ x: .3, y: .5, strength: 1, radius: .2 }], []);
    expect(warpGrid(.5, .5, [{ x: .7, y: .5, strength: 1, radius: .2 }], [])).not.toEqual(left);
  });
});
