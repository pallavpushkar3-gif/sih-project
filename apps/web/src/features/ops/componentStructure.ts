import { BoxGeometry, CylinderGeometry, DoubleSide, Group, Mesh, MeshStandardMaterial, SphereGeometry, TorusGeometry, type BufferGeometry } from "three";
import type { StructureKind } from "./componentArchitecture";

/** Authored schematic assemblies: no dimensional, damage or fault-location claim. */
export function createComponentStructure(kind: StructureKind, exploded: boolean, wireframe: boolean, color: string) {
  const group = new Group();
  group.userData = { engineeringValidated: false, units: "arbitrary scene units", kind };
  const metal = new MeshStandardMaterial({ color: "#a2b8c9", metalness: .6, roughness: .35, wireframe });
  const highlight = new MeshStandardMaterial({ color, metalness: .35, roughness: .4, wireframe });
  const dark = new MeshStandardMaterial({ color: "#334b5b", metalness: .3, roughness: .65, wireframe });
  const shell = new MeshStandardMaterial({ color: "#6e9bb4", metalness: .25, roughness: .45, transparent: true, opacity: wireframe ? 1 : .25, side: DoubleSide, wireframe, depthWrite: false });
  const spread = exploded ? 1 : 0;
  const add = (name: string, geometry: BufferGeometry, x = 0, y = 0, z = 0, material = metal) => {
    const mesh = new Mesh(geometry, material); mesh.name = name; mesh.position.set(x, y, z); group.add(mesh); return mesh;
  };
  // Cylinder longitudinal axis is X in these conceptual section views.
  const cylinder = (name: string, radius: number, length: number, x = 0, material = metal, open = false) => {
    const mesh = add(name, new CylinderGeometry(radius, radius, length, 40, 1, open), x, 0, 0, material); mesh.rotation.z = Math.PI / 2; return mesh;
  };
  const ring = (name: string, radius: number, x: number, material = metal) => { const mesh = add(name, new TorusGeometry(radius, .05, 12, 48), x, 0, 0, material); mesh.rotation.y = Math.PI / 2; };
  const ports = () => { for (const side of [-1, 1]) add("Service port", new CylinderGeometry(.12, .12, .42, 20), .35, side * .61, 0, highlight); };
  if (kind === "compressor" || kind === "turbine") {
    cylinder("Cutaway casing", .85, 2.8, 0, shell, true); cylinder("Shaft", .12, 3.9, 0, dark);
    const count = kind === "compressor" ? 5 : 3;
    for (let stage = 0; stage < count; stage++) {
      const x = (stage - (count - 1) / 2) * (.47 + spread * .22);
      cylinder("Rotor disc", .35, .09, x, highlight);
      for (let blade = 0; blade < 20; blade++) {
        const angle = blade / 20 * Math.PI * 2;
        const mesh = add("Schematic blade", new BoxGeometry(.12, .43, .1), x, Math.cos(angle) * .55, Math.sin(angle) * .55, metal);
        mesh.rotation.x = angle; mesh.rotation.y = .25;
      }
    }
    ring("Front casing flange", .86, -1.4 - spread * .65); ring("Rear casing flange", .86, 1.4 + spread * .65);
  } else if (kind === "actuator" || kind === "strut") {
    cylinder("Cylinder housing", .42, 1.8, -.4 - spread * .35, shell, true);
    cylinder("Piston", .34, .14, .3 + spread * .4, highlight); cylinder("Piston rod", .13, 2, .8 + spread * .65);
    ring("Cylinder end seal", .34, .5 + spread * .3, dark);
    for (const x of [-1.65 - spread * .4, 1.95 + spread * .65]) ring("Attachment eye", .22, x);
    ports();
  } else if (kind === "tyre" || kind === "brake") {
    cylinder("Wheel hub", .3, .7, 0, dark);
    if (kind === "tyre") { const tyre = add("Tyre", new TorusGeometry(.8, .25, 24, 64), -spread * .9, 0, 0, dark); tyre.rotation.y = Math.PI / 2; cylinder("Rim", .64, .33, spread * .6); }
    else { for (let i = 0; i < 5; i++) cylinder("Brake disc", .85, .055, (i - 2) * (.13 + spread * .19), i % 2 ? highlight : metal); add("Caliper", new BoxGeometry(.65, .4, .45), 0, 1.05 + spread * .6, 0, highlight); }
    cylinder("Axle", .12, 2.8);
  } else if (kind === "electronics" || kind === "battery") {
    add("Enclosure", new BoxGeometry(2.4, 1.2, 1.65), 0, -.1, 0, shell);
    add("Cover", new BoxGeometry(2.4, .09, 1.65), 0, .55 + spread * .85, 0, metal);
    if (kind === "battery") { for (let i = 0; i < 6; i++) add("Cell module", new CylinderGeometry(.23, .23, .9, 24), (i % 3 - 1) * .6, .04 + spread * .18, (Math.floor(i / 3) - .5) * .64, highlight); }
    else { add("Circuit board", new BoxGeometry(2.1, .06, 1.35), 0, .05 + spread * .2, 0, highlight); for (let i = 0; i < 8; i++) add("Schematic module", new BoxGeometry(.28, .15, .27), (i % 4 - 1.5) * .44, .16 + spread * .2, (Math.floor(i / 4) - .5) * .65, dark); }
    for (const x of [-.7, .7]) add("Connector", new CylinderGeometry(.12, .12, .25, 16), x, .7 + spread * .85, .25, metal);
  } else if (kind === "cooling") {
    add("Core", new BoxGeometry(1.8, .9, 1.35), 0, 0, 0, highlight);
    for (let i = 0; i < 16; i++) add("Cooling fin", new BoxGeometry(.035, 1.15, 1.55), (i - 7.5) * .13, spread * .35, 0, metal);
    for (const side of [-1, 1]) add("Manifold", new BoxGeometry(.25, 1.2, 1.6), side * (1.15 + spread * .5), 0, 0, dark);
    ports();
  } else if (kind === "sensor") {
    cylinder("Sensor body", .4, 1.2, -.3, shell); cylinder("Probe", .09, 1.65, .95 + spread * .45, highlight);
    cylinder("Connector", .27, .3, -1.15 - spread * .6, dark); ring("Mounting flange", .5, .32);
  } else {
    cylinder("Sectioned housing", .65, 1.7, 0, shell, true);
    if (kind === "filter") { for (let i = 0; i < 28; i++) { const angle = i / 28 * Math.PI * 2; add("Filter pleat", new BoxGeometry(1.4, .13, .025), 0, Math.cos(angle) * .44, Math.sin(angle) * .44, highlight).rotation.x = angle; } }
    else if (kind === "reservoir") { cylinder("Pickup tube", .07, 1.6, 0, highlight); add("Service float", new SphereGeometry(.23, 24, 16), .3, .1, 0, dark); }
    else { cylinder("Drive shaft / spool", .16, 2.65, 0, dark); cylinder("Rotor / spool core", .42, kind === "generator" ? 1.3 : .4, spread * .45, highlight); for (let i = 0; i < 10; i++) { const angle = i / 10 * Math.PI * 2; add("Rotor vane", new BoxGeometry(kind === "generator" ? 1.3 : .16, .25, .04), spread * .45, Math.cos(angle) * .44, Math.sin(angle) * .44, metal).rotation.x = angle; } }
    ring("End cap", .66, -.9 - spread * .6); ring("End cap", .66, .9 + spread * .6); if (kind !== "generator") ports();
  }
  return group;
}
