import { BufferGeometry, CatmullRomCurve3, CircleGeometry, Color, CylinderGeometry, DoubleSide, ExtrudeGeometry, Float32BufferAttribute, Group, InstancedMesh, Matrix4, Mesh, MeshPhysicalMaterial, MeshStandardMaterial, Quaternion, Shape, SphereGeometry, TorusGeometry, TubeGeometry, Vector3 } from "three";

// Authored visual geometry, not engineering CAD. Arbitrary scene units and
// stylised Tejas-inspired proportions must never be used for installation/physics.
type Point = [number, number, number];
type Station = [number, number, number, number]; // z, horizontal radius, vertical radius, centre height

function loft(stations: Station[], segments = 96, sides = 64) {
  const profile = new CatmullRomCurve3(stations.map(([z, rx, ry]) => new Vector3(rx, ry, z)), false, "catmullrom", .25);
  const centres = new CatmullRomCurve3(stations.map(([z, , , cy]) => new Vector3(0, cy, z)), false, "catmullrom", .25);
  const vertices: number[] = [], indices: number[] = [];
  for (let i = 0; i <= segments; i++) {
    const p = profile.getPoint(i / segments), c = centres.getPoint(i / segments);
    for (let j = 0; j <= sides; j++) {
      const angle = j / sides * Math.PI * 2;
      vertices.push(Math.cos(angle) * Math.max(.001, p.x), c.y + Math.sin(angle) * Math.max(.001, p.y), p.z);
      if (i < segments && j < sides) {
        const a = i * (sides + 1) + j, b = a + sides + 1;
        indices.push(a, a + 1, b, a + 1, b + 1, b);
      }
    }
  }
  const geometry = new BufferGeometry();
  geometry.setAttribute("position", new Float32BufferAttribute(vertices, 3)); geometry.setIndex(indices); geometry.computeVertexNormals();
  return geometry;
}

export function createFighterVisual() {
  const root = new Group(); root.name = "Tejas-inspired illustrative fighter";
  root.userData = { modelKind: "illustrative-fighter", revision: "visual-v1", engineeringValidated: false, units: "arbitrary scene units", source: "Authored procedural geometry; public silhouette inspiration only" };
  const paint = new MeshStandardMaterial({ color: "#8394a3", metalness: .38, roughness: .48 });
  const edge = new MeshStandardMaterial({ color: "#657584", metalness: .42, roughness: .43 });
  const nose = new MeshStandardMaterial({ color: "#526171", metalness: .15, roughness: .61 });
  const seam = new MeshStandardMaterial({ color: "#3c4c5b", roughness: .75 });
  const chrome = new MeshStandardMaterial({ color: "#b5c3cf", metalness: .88, roughness: .24 });
  const graphite = new MeshStandardMaterial({ color: "#151d26", roughness: .84 });
  const hotMetal = new MeshStandardMaterial({ color: "#726c65", metalness: .86, roughness: .38, side: DoubleSide });
  const glass = new MeshPhysicalMaterial({ color: "#233f58", metalness: .12, roughness: .09, transparent: true, opacity: .73, clearcoat: 1, clearcoatRoughness: .06, side: DoubleSide });
  const add = (name: string, geometry: BufferGeometry, material: MeshStandardMaterial, position: Point = [0, 0, 0], rotation: Point = [0, 0, 0], scale: Point = [1, 1, 1]) => {
    const mesh = new Mesh(geometry, material); mesh.name = name; mesh.position.set(...position); mesh.rotation.set(...rotation); mesh.scale.set(...scale); mesh.castShadow = true; mesh.receiveShadow = true; root.add(mesh); return mesh;
  };
  const rod = (name: string, a: Point, b: Point, radius: number, material = chrome) => {
    const start = new Vector3(...a), end = new Vector3(...b), delta = end.clone().sub(start);
    const mesh = add(name, new CylinderGeometry(radius, radius, delta.length(), 12), material);
    mesh.position.copy(start.add(end).multiplyScalar(.5)); mesh.quaternion.copy(new Quaternion().setFromUnitVectors(new Vector3(0, 1, 0), delta.normalize()));
  };
  const line = (name: string, points: Point[], radius = .006, material = seam) => add(name, new TubeGeometry(new CatmullRomCurve3(points.map(p => new Vector3(...p))), Math.max(16, points.length * 12), radius, 6, false), material);
  const plate = (name: string, points: [number, number][], material: MeshStandardMaterial, height = .06) => {
    const shape = new Shape(); points.forEach(([x, z], i) => i ? shape.lineTo(x, z) : shape.moveTo(x, z)); shape.closePath();
    return add(name, new ExtrudeGeometry(shape, { depth: height, bevelEnabled: true, bevelThickness: .012, bevelSize: .012, bevelSegments: 2, steps: 1 }), material, [0, height / 2, 0], [Math.PI / 2, 0, 0]);
  };

  add("Continuous shaped fuselage", loft([[-4.45, .44, .4, -.02], [-3.8, .49, .43, 0], [-2.4, .59, .48, .02], [-.9, .65, .47, .02], [.4, .61, .43, .02], [1.65, .44, .36, .05], [2.85, .31, .27, .06]]), paint);
  add("Tapered radar nose visual", loft([[2.85, .31, .27, .06], [3.65, .23, .2, .045], [4.35, .13, .12, .01], [4.95, .014, .016, -.025]], 64), nose);
  rod("Nose pitot visual", [0, -.025, 4.88], [0, -.055, 5.46], .013, chrome);
  for (let side = -1; side <= 1; side += 2) {
    plate(`Compound delta wing ${side}`, [[side * .48, 1.05], [side * 1.2, .2], [side * 3.15, -2.85], [side * 3.08, -3.15], [side * .48, -3.62]], paint, .085);
    plate(`Separate elevon surface ${side}`, [[side * .8, -3.42], [side * 2.85, -3.05], [side * 2.45, -2.7], [side * .83, -2.94]], edge, .088);
    line(`Leading edge joint ${side}`, [[side * .61, .067, .86], [side * 1.2, .067, .13], [side * 3.06, .067, -2.85]]);
    line(`Elevon hinge ${side}`, [[side * .85, .067, -2.96], [side * 1.65, .067, -2.83], [side * 2.45, .067, -2.7]]);
    line(`Wing access panel ${side}`, [[side * 1.05, .065, -1.3], [side * 1.65, .065, -1.68], [side * 1.63, .065, -2.25], [side * 1.02, .065, -2.25], [side * 1.05, .065, -1.3]]);
    line(`Outer wing panel ${side}`, [[side * 1.85, .063, -1.5], [side * 2.75, .063, -2.88]]);
    const intake = add(`Intake fairing ${side}`, new CylinderGeometry(.29, .31, 1.24, 48, 1, true), paint, [side * .64, -.095, .36], [Math.PI / 2, 0, 0], [1, 1, .92]);
    intake.name = `Side intake fairing ${side}`;
    add(`Dark recessed intake mouth ${side}`, new CircleGeometry(.263, 48), graphite, [side * .64, -.095, .98], [0, 0, 0], [1, .9, 1]);
    add(`Intake rolled lip ${side}`, new TorusGeometry(.278, .025, 10, 48), chrome, [side * .64, -.095, 1], [0, 0, 0], [1, .9, 1]);
    rod(`Intake splitter ${side}`, [side * .4, -.3, 1.02], [side * .4, .14, 1.02], .019, edge);
    for (const x of [1.18, 2.03]) {
      const pylon = plate(`Empty underwing pylon ${side}-${x}`, [[side * (x - .04), -1.6], [side * (x + .04), -1.6], [side * (x + .055), -2.57], [side * (x - .055), -2.57]], edge, .24);
      pylon.position.y = -.16;
      rod(`Pylon rail ${side}-${x}`, [side * x, -.3, -1.7], [side * x, -.3, -2.5], .027, chrome);
    }
    add(`Wingtip navigation lens ${side}`, new SphereGeometry(.035, 12, 8), new MeshStandardMaterial({ color: side === -1 ? "#b74743" : "#409872", emissive: side === -1 ? "#611c19" : "#143d29", emissiveIntensity: .25 }), [side * 3.12, .035, -2.88]);
  }

  const fin = new Shape(); fin.moveTo(1.5, .36); fin.lineTo(3.18, 1.98); fin.lineTo(3.95, 1.79); fin.lineTo(4.22, .32); fin.closePath();
  add("Single swept vertical fin", new ExtrudeGeometry(fin, { depth: .075, bevelEnabled: true, bevelSize: .015, bevelThickness: .012, bevelSegments: 2 }), paint, [-.038, 0, 0], [0, Math.PI / 2, 0]);
  line("Fin rudder seam", [[.054, .48, -3.91], [.054, 1.67, -3.71]], .007);
  line("Fin leading seam", [[.052, .49, -1.8], [.052, 1.8, -3.2]], .007);
  add("Cockpit glazed canopy", new SphereGeometry(1, 64, 32, 0, Math.PI * 2, 0, Math.PI / 2), glass, [0, .365, 1.69], [0, 0, 0], [.355, .53, 1.03]);
  const rim: Point[] = Array.from({ length: 65 }, (_, i) => { const a = i / 64 * Math.PI * 2; return [Math.cos(a) * .357, .371, 1.69 + Math.sin(a) * 1.035]; });
  line("Canopy perimeter frame", rim, .022, edge);
  for (const z of [1.02, 2.32]) {
    const arc: Point[] = Array.from({ length: 25 }, (_, i) => { const a = i / 24 * Math.PI; const f = Math.sqrt(1 - ((z - 1.69) / 1.03) ** 2); return [Math.cos(a) * .36 * f, .372 + Math.sin(a) * .53 * f, z]; });
    line(`Canopy transverse frame ${z}`, arc, .017, chrome);
  }
  add("Cockpit seat headrest", new CylinderGeometry(.13, .16, .32, 12), graphite, [0, .53, 1.37], [.1, 0, 0], [1, 1, .75]);
  add("Instrument coaming", new SphereGeometry(1, 24, 12), graphite, [0, .39, 2.1], [0, 0, 0], [.28, .15, .29]);
  line("Dorsal spine seam", [[0, .48, .58], [0, .53, -.6], [0, .52, -1.7], [0, .47, -2.7]], .018, edge);
  for (const z of [-.1, -1.2]) {
    rod(`Dorsal antenna ${z}`, [0, .49, z], [0, .72, z - .09], .015, graphite);
  }

  add("Exhaust dark inner cavity", new CircleGeometry(.383, 64), graphite, [0, -.02, -4.47], [0, Math.PI, 0]);
  for (const [z, radius] of [[-4.28, .455], [-4.46, .442], [-4.69, .389]]) add(`Exhaust collar ${z}`, new TorusGeometry(radius, .035, 12, 64), hotMetal, [0, -.02, z]);
  for (let i = 0; i < 18; i++) {
    const a = i / 18 * Math.PI * 2, b = (i + .9) / 18 * Math.PI * 2;
    const geometry = new BufferGeometry();
    geometry.setAttribute("position", new Float32BufferAttribute([Math.cos(a) * .44, Math.sin(a) * .44 - .02, -4.43, Math.cos(b) * .44, Math.sin(b) * .44 - .02, -4.43, Math.cos(a) * .375, Math.sin(a) * .375 - .02, -4.77, Math.cos(b) * .375, Math.sin(b) * .375 - .02, -4.77], 3));
    geometry.setIndex([0, 1, 2, 1, 3, 2]); geometry.computeVertexNormals(); add(`Individual exhaust petal ${i}`, geometry, i % 2 ? chrome : hotMetal);
  }

  // Tricycle gear, tyres, hubs, hydraulic oleos, braces and separate bay doors.
  const wheel = (name: string, position: Point, radius: number, width: number) => {
    add(`${name} tyre`, new TorusGeometry(radius, width, 16, 40), graphite, position, [0, Math.PI / 2, 0]);
    add(`${name} hub`, new CylinderGeometry(radius * .66, radius * .66, width * 1.6, 32), chrome, position, [0, 0, Math.PI / 2]);
    for (let i = 0; i < 8; i++) { const a = i / 8 * Math.PI * 2; rod(`${name} hub spoke ${i}`, [position[0] + width, position[1], position[2]], [position[0] + width, position[1] + Math.cos(a) * radius * .59, position[2] + Math.sin(a) * radius * .59], .011, edge); }
  };
  for (const side of [-1, 1]) {
    wheel(`Main gear ${side}`, [side * .81, -1.12, -1.68], .24, .08);
    rod(`Main oleo housing ${side}`, [side * .52, -.33, -1.48], [side * .77, -.86, -1.62], .045, edge);
    rod(`Main polished piston ${side}`, [side * .77, -.8, -1.62], [side * .81, -1.12, -1.68], .026);
    rod(`Main drag brace ${side}`, [side * .51, -.4, -2.35], [side * .8, -.98, -1.68], .019);
    rod(`Main torque link ${side}`, [side * .77, -.76, -1.62], [side * .87, -.91, -1.51], .014);
    rod(`Main torque return ${side}`, [side * .87, -.91, -1.51], [side * .81, -1.05, -1.68], .014);
    const door = plate(`Main bay door ${side}`, [[side * .48, -1.25], [side * .8, -1.38], [side * .85, -2.2], [side * .5, -2.3]], paint, .026); door.position.y = -.53;
  }
  wheel("Nose gear", [0, -1.2, 2.55], .17, .064);
  rod("Nose oleo housing", [0, -.25, 2.65], [0, -.77, 2.55], .035, edge);
  rod("Nose polished piston", [0, -.72, 2.55], [0, -1.2, 2.55], .023);
  rod("Nose rear brace", [0, -.3, 1.98], [0, -.96, 2.55], .018);
  for (const side of [-1, 1]) {
    rod(`Nose fork ${side}`, [0, -1.05, 2.55], [side * .1, -1.2, 2.55], .019);
    const door = plate(`Nose bay door ${side}`, [[side * .06, 2.2], [side * .17, 2.2], [side * .17, 2.9], [side * .06, 2.9]], edge, .023); door.position.y = -.39;
  }

  // Fine fastening detail is instanced rather than hundreds of draw calls.
  const fasteners: Point[] = [];
  for (const side of [-1, 1]) {
    for (let i = 0; i < 35; i++) { const t = i / 34; fasteners.push([side * (.7 + t * 2.35), .066, .75 - t * 3.6], [side * (.8 + t * 2.03), .066, -3.42 + t * .37]); }
    for (const z of [-2.8, -2, -.8]) for (let i = 0; i < 10; i++) { const a = i / 9 * Math.PI * .75; fasteners.push([side * Math.sin(a) * .57, Math.cos(a) * .47 + .025, z]); }
  }
  const bolts = new InstancedMesh(new SphereGeometry(.008, 6, 4), edge, fasteners.length); bolts.name = "Instanced panel fasteners";
  fasteners.forEach((p, i) => bolts.setMatrixAt(i, new Matrix4().makeTranslation(...p))); root.add(bolts);
  const colours = ["#ca6e36", "#eef1ed", "#3c7c55"];
  for (const side of [-1, 1]) {
    colours.forEach((colour, i) => add(`Decorative roundel ${side}-${i}`, new CircleGeometry(.2 - i * .056, 40), new MeshStandardMaterial({ color: new Color(colour), roughness: .8 }), [side * 1.83, .065 + i * .002, -2.32], [-Math.PI / 2, 0, 0]));
  }
  return root;
}
