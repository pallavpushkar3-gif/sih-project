import { Suspense, useCallback, useEffect, useMemo, useState, type Dispatch, type SetStateAction } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls, useGLTF } from "@react-three/drei";
import { Box3, EdgesGeometry, Group, InstancedMesh, LineBasicMaterial, LineSegments, Mesh, PerspectiveCamera, Vector3 } from "three";
import { architectureColor, type ArchitectureComponent } from "./componentArchitecture";
import { createComponentStructure } from "./componentStructure";
import { fittedCameraPosition, modelFitPoints } from "./cameraFit";
import { stateLabel } from "./format";

function Fit({ model, reset, onReady }: { model: Group; reset: string; onReady: () => void }) {
  const { camera, size, invalidate } = useThree();
  const points = useMemo(() => modelFitPoints(model), [model]);
  const direction = useMemo(() => new Vector3(5, 3, 6), []);
  useEffect(onReady, [onReady]);
  useEffect(() => {
    if (!(camera instanceof PerspectiveCamera)) return;
    camera.position.copy(fittedCameraPosition(direction, points, camera.fov, size.width / size.height, .8));
    camera.lookAt(0, 0, 0); invalidate();
  }, [camera, size.width, size.height, points, reset, direction, invalidate]);
  return <OrbitControls makeDefault enablePan={false} enableZoom={false} enableDamping={false} target={[0, 0, 0]} onChange={() => {
    if (!(camera instanceof PerspectiveCamera)) return;
    camera.position.copy(fittedCameraPosition(camera.position, points, camera.fov, size.width / size.height, .8));
    camera.lookAt(0, 0, 0);
  }}/>;
}
function ContextStatus({ onLost }: { onLost: () => void }) {
  const { gl } = useThree();
  useEffect(() => {
    const lost = (event: Event) => { event.preventDefault(); onLost(); };
    gl.domElement.addEventListener("webglcontextlost", lost);
    return () => gl.domElement.removeEventListener("webglcontextlost", lost);
  }, [gl, onLost]);
  return null;
}
type ProjectedMarker = { id: string; x: number; y: number };
function AircraftLines({ components, onSelect, reset, project, onReady }: { components: ArchitectureComponent[]; onSelect: (id: string) => void; reset: string; project: Dispatch<SetStateAction<ProjectedMarker[]>>; onReady: () => void }) {
  const gltf = useGLTF(`${import.meta.env.BASE_URL}models/tejas-visual.glb`, false, false);
  const { lines, bounds, offset, scale } = useMemo(() => {
    const source = gltf.scene;
    source.updateMatrixWorld(true);
    const box = new Box3().setFromObject(source), offset = box.getCenter(new Vector3()).negate(), scale = 10 / Math.max(...box.getSize(new Vector3()).toArray());
    const lines = new Group(), material = new LineBasicMaterial({ color: "#cce9ff", transparent: true, opacity: .65 });
    source.traverse(object => {
      if (!(object instanceof Mesh) || object instanceof InstancedMesh || /fastener|spoke|roundel|petal/i.test(object.name)) return;
      const geometry = new EdgesGeometry(object.geometry, /fuselage|nose|glazed canopy/i.test(object.name) ? 3 : 35);
      geometry.applyMatrix4(object.matrixWorld); geometry.translate(offset.x, offset.y, offset.z); geometry.scale(scale, scale, scale);
      lines.add(new LineSegments(geometry, material));
    });
    // Bounds need meshes for modelFitPoints; the shared source is not mutated.
    const bounds = source.clone(true); bounds.position.copy(offset.clone().multiplyScalar(scale)); bounds.scale.setScalar(scale);
    return { lines, bounds, offset, scale };
  }, [gltf.scene]);
  useEffect(() => () => {
    lines.traverse(object => { if (object instanceof LineSegments) { object.geometry.dispose(); object.material.dispose(); } });
  }, [lines]);
  const positions = useMemo(() => components.filter(item => item.layout).map(item => ({ id: item.id, point: new Vector3(...item.layout!.position).add(offset).multiplyScalar(scale) })), [components, offset, scale]);
  useFrame(({ camera }) => {
    const next = positions.map(item => { const point = item.point.clone().project(camera); return { id: item.id, x: (point.x + 1) * 50, y: (1 - point.y) * 50 }; });
    project(previous => previous.length === next.length && next.every((item, index) => item.id === previous[index].id && Math.abs(item.x - previous[index].x) < .02 && Math.abs(item.y - previous[index].y) < .02) ? previous : next);
  });
  return <><primitive object={lines} dispose={null}/><Fit model={bounds} reset={reset} onReady={onReady}/>
    {components.filter(item => item.layout).map(item => {
      const point = new Vector3(...item.layout!.position).add(offset).multiplyScalar(scale);
      return <mesh key={item.id} position={point} onClick={event => { event.stopPropagation(); onSelect(item.id); }}>
        <sphereGeometry args={[.14, 20, 16]}/><meshBasicMaterial color={architectureColor(item)} depthTest={false}/>
      </mesh>;
    })}</>;
}
function Part({ component, mode, reset, onReady }: { component: ArchitectureComponent; mode: "assembled" | "exploded" | "wireframe"; reset: string; onReady: () => void }) {
  const model = useMemo(() => createComponentStructure(component.layout!.kind, mode === "exploded", mode === "wireframe", architectureColor(component)), [component, mode]);
  useEffect(() => () => {
    model.traverse(object => { if (object instanceof Mesh) { object.geometry.dispose(); (Array.isArray(object.material) ? object.material : [object.material]).forEach(material => material.dispose()); } });
  }, [model]);
  return <><primitive object={model} dispose={null}/><Fit model={model} reset={reset} onReady={onReady}/></>;
}
export function BlueprintStudio({ components, selected, onSelect, mode = "assembled", reset = "0" }: {
  components: ArchitectureComponent[]; selected?: ArchitectureComponent; onSelect?: (id: string) => void; mode?: "assembled" | "exploded" | "wireframe"; reset?: string;
}) {
  const [lost, setLost] = useState(false);
  const [projected, setProjected] = useState<ProjectedMarker[]>([]);
  const [ready, setReady] = useState(false);
  const onReady = useCallback(() => setReady(true), []);
  useEffect(() => { if (ready) return; const timer = setTimeout(() => setLost(true), 20_000); return () => clearTimeout(timer); }, [ready]);
  if (lost) return <p className="bp-renderer-fallback" role="status">3D view unavailable. Component records and evidence remain available.</p>;
  return <><Canvas frameloop="demand" dpr={[1, 1.5]} camera={{ position: [5, 3, 6], fov: 35 }} gl={{ alpha: true, antialias: true }}>
    <ContextStatus onLost={() => setLost(true)}/><ambientLight intensity={1.4}/><directionalLight position={[4, 8, 6]} intensity={2.3}/><directionalLight position={[-4, 2, -5]} intensity={1}/>
    <Suspense fallback={null}>{selected?.layout ? <Part component={selected} mode={mode} reset={reset} onReady={onReady}/> : <AircraftLines components={components} onSelect={onSelect ?? (() => undefined)} reset={reset} project={setProjected} onReady={onReady}/>}</Suspense>
  </Canvas>{!ready && <p className="bp-scene-loading" role="status">Preparing 3D structure…</p>}{!selected && projected.map(position => {
    const item = components.find(component => component.id === position.id);
    return item && <button key={item.id} type="button" className="bp-spatial-target" style={{ left: `${position.x}%`, top: `${position.y}%`, borderColor: architectureColor(item), background: item.attention ? "#cb3543" : "#163e5d" }} aria-label={`Inspect ${item.name}: ${stateLabel[item.state]}`} onClick={() => onSelect?.(item.id)}>{item.number}</button>;
  })}</>;
}
