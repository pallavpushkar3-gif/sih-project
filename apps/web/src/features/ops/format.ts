import type { HealthState } from "./api";

export const stateLabel: Record<HealthState, string> = {
  healthy: "Healthy", watch: "Watch", degraded: "Degraded", critical: "Critical", failed: "Failed", under_maintenance: "In maintenance",
};
export const stateRank: Record<HealthState, number> = { healthy: 0, watch: 1, degraded: 2, critical: 3, failed: 4, under_maintenance: 4 };
export const availabilityLabel: Record<string, string> = {
  available: "Available", scheduled_maintenance: "Scheduled maintenance", unscheduled_repair: "Unscheduled repair",
  awaiting_spares: "Awaiting spares", awaiting_agency: "Awaiting agency", scheduled: "Scheduled", unscheduled: "Unscheduled",
};
export const causeColorVar: Record<string, string> = {
  scheduled_maintenance: "--o-maint", scheduled: "--o-maint", unscheduled_repair: "--o-critical", unscheduled: "--o-critical",
  awaiting_spares: "--o-degraded", awaiting_agency: "--o-watch",
};
export const actionTone: Record<string, string> = { ground_now: "critical", replace_within: "degraded", inspect: "watch", monitor: "healthy" };
export const factorLabel: Record<string, string> = {
  failure_risk: "Failure risk", criticality: "Criticality", remaining_life: "Remaining life", spare_shortfall: "Spare shortfall", availability_impact: "Availability impact",
};
export const scenarioLabel: Record<string, string> = {
  schedule_maintenance: "Schedule maintenance", spare_unavailable: "Critical spare unavailable", early_replacement: "Address predicted failures early", extra_capacity: "Add bay capacity",
};

export const pct = (value: number | null | undefined, digits = 0) => value === null || value === undefined ? "—" : `${(value * 100).toFixed(digits)}%`;
export const num = (value: number | null | undefined, digits = 0) => value === null || value === undefined ? "—" : value.toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: digits });
export const signed = (value: number, digits = 1, unit = "") => `${value > 0 ? "+" : value < 0 ? "−" : "±"}${Math.abs(value).toFixed(digits)}${unit}`;
export function shortDate(iso: string | null | undefined) {
  if (!iso) return "—";
  return new Date(`${iso.slice(0, 10)}T00:00:00Z`).toLocaleDateString(undefined, { day: "numeric", month: "short", timeZone: "UTC" });
}
export function longDate(iso: string | null | undefined) {
  if (!iso) return "—";
  return new Date(`${iso.slice(0, 10)}T00:00:00Z`).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
}
export function rulText(rul: { p10: number; p50: number; p90: number }) {
  if (rul.p50 >= 59.5) return "≥ 60 days";
  return `${rul.p50.toFixed(0)} d (${rul.p10.toFixed(0)}–${rul.p90 >= 59.5 ? "60+" : rul.p90.toFixed(0)})`;
}
export function cssVar(name: string) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || "#888";
}
export function stateColor(state: string) { return cssVar(`--o-${state === "under_maintenance" ? "maint" : state}`); }
