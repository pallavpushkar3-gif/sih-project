import { Box3, Mesh, Vector3, type Material } from "three";
import { describe, expect, it } from "vitest";
import { createFighterVisual } from "./fighterGeometry";

describe("authored illustrative fighter geometry", () => {
  it("has finite nonempty surfaces, symmetric delta wings and valid front/rear features", () => {
    const model = createFighterVisual();
    const bounds = new Box3().setFromObject(model), size = bounds.getSize(new Vector3());
    expect(size.z).toBeGreaterThan(size.x);
    expect(size.x).toBeGreaterThan(6);
    expect(model.userData.engineeringValidated).toBe(false);
    model.traverse(object => {
      if (!(object instanceof Mesh)) return;
      const positions = object.geometry.getAttribute("position");
      expect(positions.count, object.name).toBeGreaterThan(2);
      expect([...positions.array].every(Number.isFinite), object.name).toBe(true);
      const normals = object.geometry.getAttribute("normal");
      expect([...normals.array].every(Number.isFinite), object.name).toBe(true);
    });
    const left = new Box3().setFromObject(model.getObjectByName("Compound delta wing -1")!);
    const right = new Box3().setFromObject(model.getObjectByName("Compound delta wing 1")!);
    expect(left.min.x).toBeCloseTo(-right.max.x, 4);
    expect(left.max.x).toBeCloseTo(-right.min.x, 4);
    expect(left.min.z).toBeCloseTo(right.min.z, 4);
    expect(left.max.z).toBeCloseTo(right.max.z, 4);
    expect(model.getObjectByName("Nose pitot visual")!.position.z).toBeGreaterThan(4);
    expect(model.getObjectByName("Exhaust dark inner cavity")!.position.z).toBeLessThan(-4);
    expect(model.getObjectByName("Cockpit glazed canopy")!.position.y).toBeGreaterThan(0);
    expect(model.getObjectByName("Main gear 1 tyre")!.position.y).toBeLessThan(-1);
    const materials = new Set<Material>();
    model.traverse(object => { if (object instanceof Mesh) { object.geometry.dispose(); (Array.isArray(object.material) ? object.material : [object.material]).forEach(material => materials.add(material)); } });
    materials.forEach(material => material.dispose());
  });
});
