import type { components } from "./generated/schema";

export type FleetItem = components["schemas"]["FleetItemResponse"];
export type Assessment = components["schemas"]["AssessmentSummaryResponse"];
export type ComponentDetail = components["schemas"]["ComponentDetailResponse"];
export type Plan = components["schemas"]["PlanResponse"];
export type InventoryPart = components["schemas"]["InventoryPartResponse"];
export type Scenario = components["schemas"]["ScenarioResponse"];
export type SimulationRun = components["schemas"]["SimulationRunResponse"];
export type Alert = components["schemas"]["AlertResponse"];
export type Job = components["schemas"]["JobResponse"];

export type Validator<T> = (value: unknown) => value is T;

const base = import.meta.env.VITE_API_BASE_URL ?? "/api";

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function string(value: unknown): value is string {
  return typeof value === "string";
}

function nullableString(value: unknown): value is string | null {
  return value === null || string(value);
}

function finiteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

export function arrayOf<T>(validator: Validator<T>): Validator<T[]> {
  return (value: unknown): value is T[] => Array.isArray(value) && value.every(validator);
}

export const isFleetItem: Validator<FleetItem> = (value): value is FleetItem =>
  record(value) &&
  string(value.id) &&
  string(value.tail_number) &&
  string(value.label) &&
  string(value.provenance) &&
  Array.isArray(value.component_ids) &&
  value.component_ids.every(string) &&
  finiteNumber(value.components) &&
  finiteNumber(value.open_tasks);

export const isAlert: Validator<Alert> = (value): value is Alert =>
  record(value) &&
  string(value.id) &&
  string(value.component_id) &&
  string(value.state) &&
  string(value.reason) &&
  string(value.policy_version) &&
  nullableString(value.assessment_id) &&
  nullableString(value.acknowledged_by);

export const isInventoryPart: Validator<InventoryPart> = (value): value is InventoryPart =>
  record(value) &&
  string(value.id) &&
  string(value.name) &&
  finiteNumber(value.on_hand) &&
  finiteNumber(value.reserved) &&
  finiteNumber(value.lead_time_slots) &&
  finiteNumber(value.version) &&
  string(value.provenance);

export const isPlan: Validator<Plan> = (value): value is Plan =>
  record(value) &&
  string(value.id) &&
  string(value.status) &&
  string(value.solver_status) &&
  string(value.input_version) &&
  Array.isArray(value.assignments) &&
  value.assignments.every(
    (assignment) =>
      record(assignment) &&
      string(assignment.task_id) &&
      finiteNumber(assignment.start) &&
      finiteNumber(assignment.end),
  ) &&
  Array.isArray(value.diagnostics) &&
  value.diagnostics.every(string) &&
  string(value.created_at) &&
  nullableString(value.approved_at) &&
  nullableString(value.approved_by);

export const isScenario: Validator<Scenario> = (value): value is Scenario =>
  record(value) &&
  string(value.id) &&
  string(value.name) &&
  finiteNumber(value.version) &&
  record(value.assumptions) &&
  string(value.provenance);

export const isSimulationRun: Validator<SimulationRun> = (value): value is SimulationRun =>
  record(value) &&
  string(value.id) &&
  string(value.scenario_id) &&
  string(value.policy) &&
  finiteNumber(value.seed) &&
  finiteNumber(value.availability) &&
  value.availability >= 0 &&
  value.availability <= 1 &&
  record(value.metrics);

export const isComponentDetail: Validator<ComponentDetail> = (
  value,
): value is ComponentDetail =>
  record(value) &&
  string(value.id) &&
  string(value.aircraft_id) &&
  string(value.serial_number) &&
  string(value.kind) &&
  string(value.status) &&
  finiteNumber(value.current_cycle) &&
  Array.isArray(value.observations) &&
  value.observations.every(
    (observation) =>
      record(observation) &&
      finiteNumber(observation.cycle) &&
      string(observation.sensor) &&
      finiteNumber(observation.value) &&
      string(observation.unit) &&
      string(observation.source_version),
  ) &&
  (value.assessment === null ||
    (record(value.assessment) &&
      string(value.assessment.id) &&
      string(value.assessment.state) &&
      nullableString(value.assessment.model_version) &&
      string(value.assessment.input_version) &&
      Array.isArray(value.assessment.quality_findings)));

export async function api<T>(
  path: string,
  init?: RequestInit,
  validate?: Validator<T>,
): Promise<T> {
  const response = await fetch(`${base}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-Demo-Role": "planner",
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }
  const payload: unknown = await response.json();
  if (validate && !validate(payload)) {
    throw new Error(`API response validation failed for ${path}`);
  }
  return payload as T;
}
