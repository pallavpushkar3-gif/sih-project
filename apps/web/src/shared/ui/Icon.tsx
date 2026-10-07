import type { CSSProperties, ReactNode } from "react";
export type IconName = "aircraft" | "grid" | "bell" | "calendar" | "box" | "chart" | "search" | "arrow" | "chevron" | "refresh" | "check" | "warning" | "close" | "menu" | "clock" | "file" | "activity" | "filter" | "user"
  | "gauge" | "wrench" | "layers" | "database" | "sliders" | "sun" | "moon" | "play" | "pause" | "history" | "shield" | "spark" | "list" | "flask" | "panel" | "external" | "plus" | "info" | "trend" | "home" | "printer" | "swap";
const paths: Record<IconName, ReactNode> = {
  user: <><circle cx="12" cy="8" r="4"/><path d="M4 21v-2a8 8 0 0 1 16 0v2"/></>,
  aircraft: <><path d="m21 3-7 18-3-8-8-3 18-7Z"/><path d="m11 13 5-5"/></>,
  grid: <><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></>,
  bell: <><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9Z"/><path d="M10 21h4"/></>,
  calendar: <><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4m10-4v4M3 11h18m-14 4h3m4 0h3"/></>,
  box: <path d="m12 3 9 5v9l-9 5-9-5V8l9-5Zm0 9v10M3 8l9 4 9-4M7 5l9 5"/>,
  chart: <path d="M4 3v17h17M8 15v-4m5 4V7m5 8v-6"/>,
  search: <><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4.5 4.5"/></>,
  arrow: <path d="M4 12h16m-6-6 6 6-6 6"/>, chevron: <path d="m9 5 7 7-7 7"/>,
  refresh: <path d="M20 7a9 9 0 0 0-15-2L3 8m0-5v5h5m-4 9a9 9 0 0 0 15 2l2-3m0 5v-5h-5"/>,
  check: <path d="m5 12 4 4L19 6"/>, warning: <><path d="m12 3 10 18H2L12 3Z"/><path d="M12 9v5m0 3h.01"/></>,
  close: <path d="m6 6 12 12M6 18 18 6"/>, menu: <path d="M4 6h16M4 12h16M4 18h16"/>,
  clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>,
  file: <path d="M14 3H5v18h14V8l-5-5Zm0 0v5h5M8 12h8m-8 4h5"/>,
  activity: <path d="M2 12h5l3-8 4 16 3-8h5"/>, filter: <path d="M4 7h16M7 12h10m-7 5h4"/>,
  gauge: <><path d="M4 18a8 8 0 1 1 16 0"/><path d="m12 18 4-6"/><path d="M12 6v2M6.3 8.3l1.4 1.4M17.7 8.3l-1.4 1.4"/></>,
  wrench: <path d="M14.5 6.5a4 4 0 0 0 5 5l-9 9a2.1 2.1 0 0 1-3-3l9-9a4 4 0 0 0-2-2Z"/>,
  layers: <><path d="m12 3 9 5-9 5-9-5 9-5Z"/><path d="m3 13 9 5 9-5"/></>,
  database: <><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/></>,
  sliders: <path d="M4 6h10m4 0h2M4 12h4m4 0h8M4 18h12m4 0h0M14 4v4M8 10v4M16 16v4"/>,
  sun: <><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M2 12h2m16 0h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></>,
  moon: <path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5Z"/>,
  play: <path d="m7 4 13 8-13 8V4Z"/>, pause: <path d="M7 4h3v16H7zM14 4h3v16h-3z"/>,
  history: <><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5M12 7v5l3 2"/></>,
  shield: <path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6l-8-3Z"/>,
  spark: <path d="m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3ZM19 16l.8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8L19 16Z"/>,
  list: <path d="M9 6h11M9 12h11M9 18h11M4 6h.01M4 12h.01M4 18h.01"/>,
  flask: <path d="M9 3h6M10 3v6L4.5 18.5A1.7 1.7 0 0 0 6 21h12a1.7 1.7 0 0 0 1.5-2.5L14 9V3M7 15h10"/>,
  panel: <><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16"/></>,
  external: <path d="M14 4h6v6m0-6-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>,
  plus: <path d="M12 5v14M5 12h14"/>, info: <><circle cx="12" cy="12" r="9"/><path d="M12 11v5m0-8h.01"/></>,
  printer: <><rect x="4" y="3" width="16" height="18" rx="1.5"/><path d="M4 7h16M10 7v3h4V7M12 10v3"/><path d="M8 18h8l-1.2-3H9.2L8 18Z"/></>,
  swap: <path d="M4 8h14m-4-4 4 4-4 4M20 16H6m4-4-4 4 4 4"/>,
  trend: <path d="m3 17 6-6 4 4 8-8m0 0h-5m5 0v5"/>, home: <path d="m3 11 9-7 9 7v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1v-9Z"/>,
};
export function Icon({ name, size = 20, style }: { name: IconName; size?: number; style?: CSSProperties }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={style}>{paths[name]}</svg>;
}
