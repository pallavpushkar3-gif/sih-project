import { expect, test } from "vitest";
import { Box3, PerspectiveCamera, Vector3 } from "three";
import { createFighterVisual } from "./fighterGeometry";
import { fittedCameraPosition, modelFitPoints } from "./cameraFit";

test("the whole normalized fighter fits through arbitrary orbit angles and aspect ratios", () => {
  const model = createFighterVisual();
  const original = new Box3().setFromObject(model);
  const scale = 10 / Math.max(...original.getSize(new Vector3()).toArray());
  const center = original.getCenter(new Vector3());
  model.scale.setScalar(scale); model.position.copy(center.multiplyScalar(-scale));
  const points = modelFitPoints(model);
  for (const aspect of [.6, 1, 1.4, 2.5, 4]) for (let azimuth = 0; azimuth < 360; azimuth += 15) for (const elevation of [2, 20, 45, 70, 89]) {
    const a = azimuth * Math.PI / 180, e = elevation * Math.PI / 180;
    const direction = new Vector3(Math.cos(e) * Math.sin(a), Math.sin(e), Math.cos(e) * Math.cos(a));
    const camera = new PerspectiveCamera(32, aspect, .1, 1000);
    camera.position.copy(fittedCameraPosition(direction, points, 32, aspect));
    camera.lookAt(0, 0, 0); camera.updateMatrixWorld();
    let maxX = 0, maxY = 0, maxZ = 0;
    for (const sample of points) {
      const point = sample.clone().project(camera);
      maxX = Math.max(maxX, Math.abs(point.x)); maxY = Math.max(maxY, Math.abs(point.y)); maxZ = Math.max(maxZ, point.z);
    }
    expect(maxX).toBeLessThanOrEqual(.880001); expect(maxY).toBeLessThanOrEqual(.880001); expect(maxZ).toBeLessThan(1);
  }
});
