import type { AircraftDetail, TwinComponent } from "./api";

export type StructureKind = "compressor" | "turbine" | "pump" | "generator" | "actuator" | "filter" | "electronics" | "battery" | "brake" | "strut" | "tyre" | "sensor" | "cooling" | "valve" | "reservoir";
type Layout = { position: [number, number, number]; kind: StructureKind };
// Illustrative locations only, not verified installation coordinates. Keys are
// the implemented synthetic catalogue types, never inferred from a health score.
export const componentLayouts: Record<string, Layout> = {
  "ENG-CMP": { position: [0, .2, -.8], kind: "compressor" },
  "ENG-TRB": { position: [0, .2, -3.1], kind: "turbine" },
  "ENG-OIL": { position: [-.45, .2, -1.7], kind: "reservoir" },
  "ENG-FCU": { position: [.45, .2, -1.7], kind: "valve" },
  "HYD-PMP": { position: [-.42, .2, -.2], kind: "pump" },
  "HYD-ACT": { position: [-1.7, .12, -2.9], kind: "actuator" },
  "HYD-FLT": { position: [-.4, .2, .55], kind: "filter" },
  "ELE-GEN": { position: [.4, .2, -.65], kind: "generator" },
  "ELE-BAT": { position: [.3, .2, 1.15], kind: "battery" },
  "ELE-BUS": { position: [-.3, .2, 1.15], kind: "electronics" },
  "LG-BRK": { position: [-.81, -1.12, -1.68], kind: "brake" },
  "LG-STR": { position: [0, -.7, 2.55], kind: "strut" },
  "LG-TYR": { position: [.81, -1.12, -1.68], kind: "tyre" },
  "AVN-FCC": { position: [0, .2, 3.15], kind: "electronics" },
  "AVN-DSP": { position: [0, .55, 2.1], kind: "electronics" },
  "AVN-SNS": { position: [0, 0, 4.85], kind: "sensor" },
  "FUE-BST": { position: [1.3, .1, -1.5], kind: "pump" },
  "FUE-QTY": { position: [2.1, .1, -2.5], kind: "sensor" },
  "ECS-PCK": { position: [.4, .2, .25], kind: "cooling" },
  "ECS-PRC": { position: [-.3, .2, 1.85], kind: "valve" },
};
export type ArchitectureComponent = TwinComponent & { number: number; system: string; layout: Layout | null; attention: boolean; openAdvisories: AircraftDetail["advisories"] };
export function architectureComponents(data: AircraftDetail): ArchitectureComponent[] {
  return data.systems.flatMap(system => system.components.map(component => {
    const openAdvisories = data.advisories.filter(item => item.component_id === component.id && !["completed", "dismissed"].includes(item.status));
    return { ...component, system: system.name, layout: componentLayouts[component.type] ?? null,
      attention: ["watch", "degraded", "critical", "failed"].includes(component.state) || (component.state !== "under_maintenance" && openAdvisories.length > 0), openAdvisories };
  })).map((component, index) => ({ ...component, number: index + 1 }));
}
export const architectureColor = (component: ArchitectureComponent) => component.state === "under_maintenance" ? "#55b6ff" : component.attention ? "#ed525c" : "#76d5b1";
export const structureLabels: Record<StructureKind, string[]> = {
  compressor: ["Outer casing", "Rotor stages", "Central shaft"], turbine: ["Outer casing", "Blade discs", "Central shaft"],
  pump: ["Housing", "Rotor", "Drive shaft", "Ports"], actuator: ["Cylinder", "Piston rod", "Attachment eyes"], strut: ["Oleo housing", "Sliding piston", "Attachment eyes"],
  generator: ["Stator casing", "Rotor", "Drive shaft", "End caps"],
  filter: ["Filter housing", "Filter element", "End caps"], electronics: ["Enclosure", "Circuit board", "Connectors"], battery: ["Battery enclosure", "Cell modules", "Terminals"],
  brake: ["Brake discs", "Hub", "Caliper"], tyre: ["Tyre", "Wheel rim", "Axle"], sensor: ["Probe", "Sensor body", "Connector"],
  cooling: ["Core", "Cooling fins", "Manifolds"], valve: ["Valve body", "Spool", "Ports"], reservoir: ["Reservoir shell", "Pickup tube", "Service ports"],
};
