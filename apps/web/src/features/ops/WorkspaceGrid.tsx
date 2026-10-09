import { useEffect, useRef, useState, type RefObject } from "react";
import { FlowGrid } from "./FlowGrid";
import type { FlowSignal } from "./elasticGridMath";

export function WorkspaceGrid({ host, paused }: { host: RefObject<HTMLElement | null>; paused: boolean }) {
  const pose = useRef<FlowSignal>({ x: .5, y: .56 });
  const [reduced, setReduced] = useState(() => window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const change = () => setReduced(media.matches);
    media.addEventListener("change", change);
    return () => media.removeEventListener("change", change);
  }, []);
  return <FlowGrid stage={host} pose={pose} reduced={reduced} paused={paused} workspace/>;
}
