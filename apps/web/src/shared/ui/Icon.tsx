import type { CSSProperties, ReactNode } from "react";
export type IconName = "aircraft" | "grid" | "bell" | "calendar" | "box" | "chart" | "search" | "arrow" | "chevron" | "refresh" | "check" | "warning" | "close" | "menu" | "clock" | "file" | "activity" | "filter" | "user";
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
};
export function Icon({ name, size = 20, style }: { name: IconName; size?: number; style?: CSSProperties }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={style}>{paths[name]}</svg>;
}
