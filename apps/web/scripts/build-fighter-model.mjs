/* global Buffer, process, URL */
import { mkdir, writeFile } from "node:fs/promises";
import { GLTFExporter } from "three/addons/exporters/GLTFExporter.js";
import { createFighterVisual } from "../src/features/ops/fighterGeometry.ts";

// GLTFExporter uses FileReader even for texture-free Node export.
globalThis.FileReader = class {
  readAsArrayBuffer(blob) { blob.arrayBuffer().then(result => { this.result = result; this.onloadend?.(); }); }
  readAsDataURL(blob) { blob.arrayBuffer().then(result => { this.result = `data:${blob.type};base64,${Buffer.from(result).toString("base64")}`; this.onloadend?.(); }); }
};
const model = createFighterVisual();
const result = await new GLTFExporter().parseAsync(model, { binary: true });
if (!(result instanceof ArrayBuffer)) throw new Error("Expected binary GLB output");
const target = new URL("../public/models/tejas-visual.glb", import.meta.url);
await mkdir(new URL("../public/models/", import.meta.url), { recursive: true });
await writeFile(target, new Uint8Array(result));
let meshes = 0, triangles = 0;
model.traverse(object => { if (object.isMesh) { meshes++; triangles += object.geometry.index ? object.geometry.index.count / 3 : object.geometry.attributes.position.count / 3; } });
process.stdout.write(JSON.stringify({ path: target.pathname, bytes: result.byteLength, meshes, triangles, engineeringValidated: false }) + "\n");
