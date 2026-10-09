import { useEffect, useRef, type RefObject } from "react";
import { gridMesh, warpGrid, type FlowSignal, type GridRipple, type GridWell } from "./elasticGridMath";
import "./flow-grid.css";

/** One passive canvas, awake only while its input or surface is changing. */
export function FlowGrid({ stage, pose, reduced, paused, workspace = false }: {
  stage: RefObject<HTMLElement | null>; pose: RefObject<FlowSignal>; reduced: boolean; paused: boolean; workspace?: boolean;
}) {
  const canvas = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const element = canvas.current, host = stage.current;
    if (!element || !host) return;
    const context = element.getContext("2d");
    if (!context) return;
    const pointer = { x: .5, y: .6, strength: 0, radius: .13 }, target = { ...pointer };
    const aircraft = { x: .5, y: .56, strength: workspace ? .45 : 1.3, radius: .24 };
    const wells: GridWell[] = [aircraft, pointer];
    const ripples: (GridRipple & { started: number })[] = [];
    let mesh = gridMesh(), box = element.getBoundingClientRect();
    let width = 1, height = 1, ratio = 1;
    let frame = 0, last = 0, lastRipple = 0, visible = true, disposed = false, slow = false;
    const different = () => Math.abs(pointer.x - target.x) + Math.abs(pointer.y - target.y) + Math.abs(pointer.strength - target.strength)
      + Math.abs(aircraft.x - pose.current.x) + Math.abs(aircraft.y - pose.current.y) > .0003;
    const draw = (now: number) => {
      const started = performance.now(), dt = last ? Math.min(64, now - last) : 17;
      last = now;
      const blend = reduced ? 1 : 1 - Math.exp(-dt / 65);
      pointer.x += (target.x - pointer.x) * blend; pointer.y += (target.y - pointer.y) * blend;
      pointer.strength += (target.strength - pointer.strength) * blend;
      if (!reduced) { aircraft.x += (pose.current.x - aircraft.x) * blend; aircraft.y += (pose.current.y - aircraft.y) * blend; }
      for (let i = ripples.length - 1; i >= 0; i--) {
        ripples[i].age = (now - ripples[i].started) / 1000;
        if (ripples[i].age > 2.4) ripples.splice(i, 1);
      }
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
      context.clearRect(0, 0, width, height);
      if (pointer.strength > .005) {
        const x = pointer.x * width, y = pointer.y * height, radius = Math.min(width, height) * .22;
        const sheen = context.createRadialGradient(x, y, 0, x, y, radius);
        sheen.addColorStop(0, "rgba(172,205,220,.15)"); sheen.addColorStop(.45, "rgba(214,200,229,.09)");
        sheen.addColorStop(.7, "rgba(184,222,212,.07)"); sheen.addColorStop(1, "rgba(255,255,255,0)");
        context.globalAlpha = pointer.strength; context.fillStyle = sheen;
        context.fillRect(x - radius, y - radius, radius * 2, radius * 2);
      }
      context.globalAlpha = 1; context.beginPath();
      for (const line of mesh) for (let i = 0; i < line.length; i += 2) {
        const point = warpGrid(line[i], line[i + 1], wells, ripples);
        if (!i) context.moveTo(point.x * width, point.y * height); else context.lineTo(point.x * width, point.y * height);
      }
      context.strokeStyle = "rgba(112,151,130,.3)"; context.lineWidth = .65; context.stroke();
      if (performance.now() - started > 6) slow = true;
    };
    const allowed = () => !disposed && !reduced && !paused && !document.hidden && visible;
    const tick = (now: number) => {
      frame = 0;
      if (!allowed()) return;
      if (now - last >= (slow ? 32 : 14)) draw(now);
      if (different() || ripples.length) frame = requestAnimationFrame(tick);
    };
    const schedule = () => { if (!frame && allowed()) frame = requestAnimationFrame(tick); };
    const wake = () => { if (different()) schedule(); };
    pose.current.wake = wake;
    const resize = () => {
      box = element.getBoundingClientRect();
      width = Math.max(1, box.width); height = Math.max(1, box.height);
      ratio = Math.min(window.devicePixelRatio || 1, 1.25, 1600 / width, 1000 / height);
      element.width = Math.round(width * ratio); element.height = Math.round(height * ratio);
      mesh = gridMesh(width < 760); last = 0;
      draw(performance.now()); schedule();
    };
    const move = (event: PointerEvent) => {
      if (!allowed() || event.pointerType === "touch") return;
      target.x = Math.max(0, Math.min(1, (event.clientX - box.left) / width));
      target.y = Math.max(0, Math.min(1, (event.clientY - box.top) / height));
      target.strength = event.clientY >= box.top && event.clientY <= box.bottom ? .95 : 0;
      const now = performance.now();
      if (target.strength && now - lastRipple > 200) {
        if (ripples.length === 3) ripples.shift();
        ripples.push({ x: target.x, y: target.y, age: 0, started: now }); lastRipple = now;
      }
      schedule();
    };
    const leave = () => { target.strength = 0; schedule(); };
    const scroll = () => { box = element.getBoundingClientRect(); leave(); };
    const visibility = () => { cancelAnimationFrame(frame); frame = 0; last = 0; if (!document.hidden) schedule(); };
    const observer = new IntersectionObserver(entries => {
      visible = entries[0].isIntersecting;
      if (!visible) { cancelAnimationFrame(frame); frame = 0; last = 0; } else schedule();
    });
    const resizeObserver = new ResizeObserver(resize);
    observer.observe(element); resizeObserver.observe(element);
    host.addEventListener("pointermove", move, { passive: true }); host.addEventListener("pointerdown", move, { passive: true });
    host.addEventListener("pointerleave", leave); window.addEventListener("scroll", scroll, { passive: true });
    document.addEventListener("visibilitychange", visibility);
    resize();
    return () => {
      disposed = true; cancelAnimationFrame(frame); observer.disconnect(); resizeObserver.disconnect();
      if (pose.current.wake === wake) delete pose.current.wake;
      host.removeEventListener("pointermove", move); host.removeEventListener("pointerdown", move); host.removeEventListener("pointerleave", leave);
      window.removeEventListener("scroll", scroll); document.removeEventListener("visibilitychange", visibility);
    };
  }, [stage, pose, reduced, paused, workspace]);
  return <canvas ref={canvas} className={workspace ? "workspace-flow-grid" : "twin-flow-grid"} aria-hidden="true" data-motion={reduced ? "static" : "flow"}/>;
}
