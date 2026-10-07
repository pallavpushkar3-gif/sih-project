import { BarChart, EffectScatterChart, LineChart, ScatterChart } from "echarts/charts";
import { DataZoomComponent, GridComponent, LegendComponent, MarkAreaComponent, MarkLineComponent, MarkPointComponent, TooltipComponent } from "echarts/components";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import type { EChartsOption } from "echarts";
import { useEffect, useMemo, useRef, useState } from "react";
import { cssVar } from "./format";

echarts.use([LineChart, BarChart, ScatterChart, EffectScatterChart, GridComponent, TooltipComponent, LegendComponent, MarkAreaComponent, MarkLineComponent, MarkPointComponent, DataZoomComponent, CanvasRenderer]);

export const MONO = "Roboto Mono, ui-monospace, monospace";
export type Palette = Record<"text" | "muted" | "grid" | "surface" | "accent" | "accent2" | "healthy" | "watch" | "degraded" | "critical" | "maint" | "neutral" | "bar" | "glass", string>;

function palette(): Palette {
  return {
    text: cssVar("--o-text"), muted: cssVar("--o-text-3"), grid: cssVar("--o-border"), surface: cssVar("--o-surface"),
    accent: cssVar("--o-accent"), accent2: cssVar("--o-accent-2"), healthy: cssVar("--o-healthy"), watch: cssVar("--o-watch"),
    degraded: cssVar("--o-degraded"), critical: cssVar("--o-critical"), maint: cssVar("--o-maint"), neutral: cssVar("--o-text-3"),
    bar: cssVar("--o-chart-bar"), glass: cssVar("--o-glass"),
  };
}

/** Re-renders when the theme attribute on <html> changes so canvas colours follow CSS tokens. */
export function usePalette() {
  const [value, setValue] = useState(palette);
  useEffect(() => {
    const observer = new MutationObserver(() => setValue(palette()));
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => observer.disconnect();
  }, []);
  return value;
}

export function baseAxes(p: Palette) {
  return {
    axisLine: { show: false, lineStyle: { color: p.grid } },
    axisTick: { show: false },
    axisLabel: { color: p.muted, fontSize: 10.5, fontFamily: MONO },
    splitLine: { lineStyle: { color: p.grid, type: "solid" as const, opacity: 0.6 } },
  };
}
export function tooltip(p: Palette) {
  return {
    trigger: "axis" as const, backgroundColor: p.glass, borderColor: "rgba(255,255,255,.55)", borderWidth: 1, textStyle: { color: p.text, fontSize: 11.5, fontFamily: MONO },
    extraCssText: GLASS_CSS,
    axisPointer: { type: "line" as const, lineStyle: { color: p.muted, type: "solid" as const, opacity: 0.5 } },
  };
}

/** Frosted-glass look for chart tooltips (HTML overlays, so backdrop-filter applies). */
export const GLASS_CSS = "backdrop-filter:blur(16px) saturate(1.6);-webkit-backdrop-filter:blur(16px) saturate(1.6);box-shadow:0 10px 30px rgba(17,24,20,.14);border-radius:12px;padding:8px 12px;";
/** Hex colour token to rgba (canvas cannot parse color-mix). */
export function withAlpha(color: string, alpha: number) {
  const hex = color.trim().replace("#", "");
  const full = hex.length === 3 ? hex.split("").map(c => c + c).join("") : hex;
  if (!/^[0-9a-f]{6}$/i.test(full)) return color;
  const [r, g, b] = [0, 2, 4].map(i => parseInt(full.slice(i, i + 2), 16));
  return `rgba(${r},${g},${b},${alpha})`;
}
/** Soft vertical gradient under a line, fading to transparent (reference style for trend lines). */
export function areaFill(color: string, strength = 0.22) {
  const alpha = (value: number) => withAlpha(color, value);
  return { color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: alpha(strength) }, { offset: 1, color: alpha(0) }] } };
}

type Handler = (params: { dataIndex: number; seriesName?: string; name?: string; value?: unknown }) => void;
/** ``build`` returns a plain ECharts option object; ECharts validates it at runtime. */
export function OpsChart({ build, label, height = 280, onClick, deps }: { build: (p: Palette) => object; label: string; height?: number; onClick?: Handler; deps: unknown[] }) {
  const ref = useRef<HTMLDivElement>(null);
  const chart = useRef<echarts.ECharts | null>(null);
  const click = useRef(onClick);
  click.current = onClick;
  const p = usePalette();
  const option = useMemo(() => build(p), [p, ...deps]);
  useEffect(() => {
    if (!ref.current) return;
    const instance = echarts.init(ref.current, undefined, { renderer: "canvas" });
    chart.current = instance;
    instance.on("click", params => click.current?.(params as Parameters<Handler>[0]));
    const observer = new ResizeObserver(() => instance.resize());
    observer.observe(ref.current);
    return () => { observer.disconnect(); instance.dispose(); chart.current = null; };
  }, []);
  useEffect(() => {
    chart.current?.setOption({ animationDuration: 500, animationEasing: "cubicOut", textStyle: { fontFamily: "Inter, system-ui, sans-serif" }, ...option } as EChartsOption, true);
  }, [option]);
  return <div ref={ref} className={`o-chart${onClick ? " clickable" : ""}`} style={{ height }} role="img" aria-label={label}/>;
}
