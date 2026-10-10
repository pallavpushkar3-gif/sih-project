import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { Canvas, useThree, type ThreeEvent } from "@react-three/fiber";
import { OrbitControls, useGLTF } from "@react-three/drei";
import { Group, Mesh, MeshStandardMaterial, PerspectiveCamera, Vector3 } from "three";
import { architectureColor, type ArchitectureComponent } from "./componentArchitecture";
import { createComponentStructure } from "./componentStructure";
import { fittedCameraPosition, modelFitPoints } from "./cameraFit";
import { createAircraftCutaway, disposeAircraftCutaway } from "./aircraftCutaway";
export type BlueprintCamera = "perspective" | "top" | "side" | "front";

function Fit({ model, reset, onReady, view = "perspective" }: { model: Group; reset: string; onReady: () => void; view?: BlueprintCamera }) {
  const { camera, size, invalidate } = useThree();
  const points = useMemo(() => modelFitPoints(model), [model]);
  const direction = useMemo(() => view === "top" ? new Vector3(0, 12, .001) : view === "side" ? new Vector3(12, 1, 0) : view === "front" ? new Vector3(0, 1, 12) : new Vector3(7, 5, 9), [view]);
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
function AircraftCutaway({ components, onSelect, reset, onReady, view, wireframe }: { components: ArchitectureComponent[]; onSelect: (id: string) => void; reset: string; onReady: () => void; view: BlueprintCamera; wireframe: boolean }) {
  const gltf = useGLTF(`${import.meta.env.BASE_URL}models/tejas-visual.glb`, false, false);
  const model = useMemo(() => createAircraftCutaway(gltf.scene, components, wireframe), [gltf.scene, components, wireframe]);
  useEffect(() => () => disposeAircraftCutaway(model), [model]);
  const select = (event: ThreeEvent<MouseEvent>) => {
    const hit = event.intersections.find(item => typeof item.object.userData.componentId === "string");
    if (hit) { event.stopPropagation(); onSelect(hit.object.userData.componentId as string); }
  };
  return <><primitive object={model} dispose={null} onClick={select}/><Fit model={model} reset={reset} onReady={onReady} view={view}/></>;
}
function Part({ component, mode, reset, onReady }: { component: ArchitectureComponent; mode: "assembled" | "exploded" | "wireframe"; reset: string; onReady: () => void }) {
  const model = useMemo(() => createComponentStructure(component.layout!.kind, mode === "exploded", mode === "wireframe", architectureColor(component)), [component, mode]);
  useEffect(() => {
    if (component.attention && component.state !== "under_maintenance") model.traverse(object => {
      if (object instanceof Mesh) (Array.isArray(object.material) ? object.material : [object.material]).forEach(material => {
        if (material instanceof MeshStandardMaterial) material.color.set("#ed525c");
      });
    });
  }, [component, model]);
  useEffect(() => () => {
    model.traverse(object => { if (object instanceof Mesh) { object.geometry.dispose(); (Array.isArray(object.material) ? object.material : [object.material]).forEach(material => material.dispose()); } });
  }, [model]);
  return <><primitive object={model} dispose={null}/><Fit model={model} reset={reset} onReady={onReady}/></>;
}
export function BlueprintStudio({ components, selected, onSelect, mode = "assembled", reset = "0", view = "perspective", wireframe = false }: {
  components: ArchitectureComponent[]; selected?: ArchitectureComponent; onSelect?: (id: string) => void; mode?: "assembled" | "exploded" | "wireframe"; reset?: string; view?: BlueprintCamera; wireframe?: boolean;
}) {
  const [lost, setLost] = useState(false);
  const [ready, setReady] = useState(false);
  const onReady = useCallback(() => setReady(true), []);
  useEffect(() => { if (ready) return; const timer = setTimeout(() => setLost(true), 20_000); return () => clearTimeout(timer); }, [ready]);
  if (lost) return <p className="bp-renderer-fallback" role="status">3D view unavailable. Component records and evidence remain available.</p>;
  return <><Canvas frameloop="demand" dpr={[1, 1.5]} camera={{ position: [5, 3, 6], fov: 35 }} gl={{ alpha: true, antialias: true }}>
    <ContextStatus onLost={() => setLost(true)}/><ambientLight intensity={1.4}/><directionalLight position={[4, 8, 6]} intensity={2.3}/><directionalLight position={[-4, 2, -5]} intensity={1}/>
    <Suspense fallback={null}>{selected?.layout ? <Part component={selected} mode={mode} reset={reset} onReady={onReady}/> : <AircraftCutaway components={components} onSelect={onSelect ?? (() => undefined)} reset={reset} onReady={onReady} view={view} wireframe={wireframe}/>}</Suspense>
  </Canvas>{!ready && <p className="bp-scene-loading" role="status">Preparing 3D structure…</p>}</>;
}
