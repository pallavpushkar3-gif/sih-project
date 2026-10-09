export type FlowPose = { x: number; y: number };
export type FlowSignal = FlowPose & { wake?: () => void };
export type GridWell = FlowPose & { strength: number; radius: number };
export type GridRipple = FlowPose & { age: number };

/** Decorative surface displacement, in normalized stage coordinates; not a physics model. */
export function warpGrid(x: number, y: number, wells: GridWell[], ripples: GridRipple[]): FlowPose {
  let dx = 0, dy = 0;
  for (const well of wells) {
    const rx = x - well.x, ry = y - well.y;
    const influence = Math.exp(-(rx * rx + ry * ry) / (2 * well.radius * well.radius)) * well.strength;
    dx -= rx * influence * .3;
    dy += influence * .09 - ry * influence * .12;
  }
  for (const ripple of ripples) {
    if (ripple.age < 0 || ripple.age > 2.4) continue;
    const distance = Math.hypot(x - ripple.x, y - ripple.y);
    const ring = distance - ripple.age * .22;
    dy += Math.sin(ring * 55) * Math.exp(-ring * ring / .006) * Math.exp(-ripple.age * 1.5) * .012;
  }
  return { x: x + dx, y: y + dy };
}

/** Precomputed mesh; no per-frame path string generation. */
export function gridMesh(compact = false): Float32Array[] {
  const lines: Float32Array[] = [];
  const columns = compact ? 18 : 28, rows = compact ? 14 : 20;
  const line = (count: number, point: (i: number) => FlowPose) => {
    const values = new Float32Array(count * 2);
    for (let i = 0; i < count; i++) { const p = point(i); values[i * 2] = p.x; values[i * 2 + 1] = p.y; }
    return values;
  };
  for (let column = 0; column <= columns; column++) {
    lines.push(line(19, i => {
      const y = .12 + i / 18 * .98;
      return { x: .5 + (column / columns * 2 - 1) * (.3 + y * 1.2), y };
    }));
  }
  for (let row = 0; row <= rows; row++) {
    const y = .12 + (row / rows) ** 1.5 * .98;
    lines.push(line(29, i => ({ x: -.3 + i / 28 * 1.6, y })));
  }
  return lines;
}
