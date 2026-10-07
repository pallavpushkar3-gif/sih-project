"""Generic fleet hierarchy: systems, component types, monitored parameters, parts and agencies.

All names are generic engineering descriptions chosen for the synthetic demonstrator. Numerical
values are configurable modelling assumptions, not data for any real aircraft type.
"""

from dataclasses import dataclass, field, replace
from datetime import date


@dataclass(frozen=True)
class Parameter:
    name: str
    unit: str
    baseline: float
    ambient_coeff: float  # change per degree C away from 15 C
    load_coeff: float  # change per unit of load factor away from 0.7
    signature: float  # shift at full degradation signature; sign gives the degrading direction
    noise: float
    minimum: float | None = None

    @property
    def direction(self) -> int:
        return 1 if self.signature > 0 else -1


@dataclass(frozen=True)
class ComponentType:
    code: str
    system: str
    name: str
    criticality: int  # 1 (minor) .. 5 (flight critical)
    mean_life_fh: float  # mean wear-out life in flight hours (synthetic assumption)
    part_number: str
    lead_time_days: int
    unit_cost: int
    repairable: bool
    repair_days: float
    agency: str
    parameters: tuple[Parameter, ...]
    hard_time_fh: float | None = None  # preventive replacement interval, if any
    sudden_share: float = 0.15
    reorder_level: int = 2
    additive_printable: bool = False  # an AM-qualified replacement exists (Project Forge)


@dataclass(frozen=True)
class Agency:
    id: str
    name: str
    level: str
    bays: int
    capacity_hours_per_day: float
    avg_turnaround_days: float


@dataclass(frozen=True)
class Base:
    id: str
    name: str
    mean_temp_c: float
    seasonal_amplitude_c: float


@dataclass(frozen=True)
class WorldConfig:
    seed: int = 42
    aircraft: int = 40
    as_of: date = date(2026, 9, 30)
    history_days: int = 1096
    replay_days: int = 120
    live_unlabelled_days: int = 60
    dropout_rate: float = 0.03
    missing_download_rate: float = 0.005
    spike_rate: float = 0.002
    stuck_sensor_share: float = 0.02
    drift_sensor_share: float = 0.03
    inspection_interval_fh: float = 450.0
    inspection_days: int = 3
    life_scale: float = 0.62  # shortens catalog lives so the fleet shows realistic pressure
    repair_scale: float = 2.2  # active repair plus documentation, test and release
    sudden_scale: float = 0.6
    hero_ids: tuple[str, ...] = field(
        default=("AC-017", "AC-023", "AC-008", "AC-031"), repr=False
    )


SYSTEMS: tuple[tuple[str, str], ...] = (
    ("PROP", "Propulsion"),
    ("HYD", "Hydraulics"),
    ("ELEC", "Electrical"),
    ("LG", "Landing gear"),
    ("AVN", "Avionics"),
    ("FUEL", "Fuel"),
    ("ECS", "Environmental control"),
)

AGENCIES: tuple[Agency, ...] = (
    Agency("AG-LINE", "Line maintenance unit", "line", 3, 48.0, 2.5),
    Agency("AG-BASE", "Base repair workshop", "base", 2, 32.0, 6.0),
    Agency("AG-DEPOT", "Depot overhaul agency", "depot", 1, 16.0, 12.0),
)

BASES: tuple[Base, ...] = (
    Base("BASE-N", "Northern base", 9.0, 11.0),
    Base("BASE-C", "Central base", 18.0, 9.0),
    Base("BASE-S", "Southern base", 27.0, 6.0),
)


def _p(
    name: str,
    unit: str,
    baseline: float,
    signature: float,
    noise: float,
    ambient: float = 0.0,
    load: float = 0.0,
    minimum: float | None = None,
) -> Parameter:
    return Parameter(name, unit, baseline, ambient, load, signature, noise, minimum)


COMPONENT_TYPES: tuple[ComponentType, ...] = (
    ComponentType(
        "ENG-CMP", "PROP", "Compressor", 5, 3400, "PRP-210", 60, 182000, True, 4.0, "AG-DEPOT",
        (
            _p("Vibration", "ips", 0.35, 0.95, 0.05, 0.002, 0.08, 0.0),
            _p("EGT margin", "°C", 42.0, -26.0, 2.4, -0.35, -6.0),
        ),
    ),
    ComponentType(
        "ENG-TRB", "PROP", "Turbine", 5, 3600, "PRP-230", 75, 240000, True, 5.0, "AG-DEPOT",
        (
            _p("Exhaust gas temperature", "°C", 640.0, 58.0, 6.0, 1.6, 30.0),
            _p("Turbine vibration", "ips", 0.3, 0.62, 0.045, 0.0015, 0.05, 0.0),
        ),
    ),
    ComponentType(
        "ENG-OIL", "PROP", "Oil system", 4, 2200, "PRP-118", 21, 14500, True, 2.0, "AG-BASE",
        (
            _p("Oil temperature", "°C", 88.0, 19.0, 1.6, 0.42, 4.0),
            _p("Oil pressure", "psi", 62.0, -14.0, 1.4, -0.05, 2.0),
        ),
    ),
    ComponentType(
        "ENG-FCU", "PROP", "Fuel control unit", 4, 2800, "PRP-145", 40, 38000, True, 2.5,
        "AG-BASE",
        (
            _p("Fuel flow deviation", "%", 0.0, 6.2, 0.6, 0.02, 1.0),
            _p("Servo current", "mA", 42.0, 9.5, 1.2, 0.03),
        ),
    ),
    ComponentType(
        "HYD-PMP", "HYD", "Main hydraulic pump", 4, 2400, "HYD-114", 45, 26800, True, 2.0,
        "AG-BASE",
        (
            _p("Outlet pressure", "psi", 3000.0, -215.0, 18.0, -0.8, -12.0),
            _p("Pressure oscillation", "psi", 22.0, 56.0, 3.0, 0.05, 2.0, 0.0),
            _p("Fluid temperature", "°C", 58.0, 17.0, 1.5, 0.55, 3.0),
        ),
        reorder_level=1,
    ),
    ComponentType(
        "HYD-ACT", "HYD", "Flight-control actuator", 3, 3000, "HYD-162", 30, 17400, True, 1.5,
        "AG-BASE",
        (
            _p("Response time", "ms", 118.0, 40.0, 4.0, 0.12, 6.0),
            _p("Internal leakage", "L/min", 0.3, 1.4, 0.08, 0.002, 0.0, 0.0),
        ),
    ),
    ComponentType(
        "HYD-FLT", "HYD", "Reservoir and filter", 2, 1700, "HYD-020", 10, 1200, False, 0.5,
        "AG-LINE",
        (_p("Filter differential pressure", "psid", 18.0, 31.0, 1.5, 0.03, 2.0, 0.0),),
        hard_time_fh=1200.0, reorder_level=3,
    ),
    ComponentType(
        "ELE-GEN", "ELEC", "Generator", 4, 2600, "ELE-301", 35, 31000, True, 1.5, "AG-BASE",
        (
            _p("Output voltage", "V", 115.0, -4.6, 0.4, -0.01, -0.5),
            _p("Voltage ripple", "V", 1.2, 3.3, 0.15, 0.004, 0.2, 0.0),
            _p("Winding temperature", "°C", 92.0, 21.0, 2.0, 0.5, 5.0),
        ),
    ),
    ComponentType(
        "ELE-BAT", "ELEC", "Main battery", 3, 2300, "ELE-050", 14, 4200, False, 0.5, "AG-LINE",
        (
            _p("Internal resistance", "mΩ", 24.0, 18.0, 0.9, -0.06),
            _p("Charge acceptance", "%", 97.0, -22.0, 1.0, 0.05),
        ),
        hard_time_fh=2000.0, reorder_level=3,
    ),
    ComponentType(
        "ELE-BUS", "ELEC", "Bus power controller", 3, 3600, "ELE-212", 28, 12800, True, 1.0,
        "AG-LINE",
        (
            _p("Bus voltage deviation", "V", 0.2, 2.6, 0.18, 0.002, 0.0, 0.0),
            _p("Built-in-test messages", "per flight", 0.05, 1.6, 0.1, 0.0, 0.0, 0.0),
        ),
    ),
    ComponentType(
        "LG-BRK", "LG", "Brake assembly", 4, 1900, "LDG-404", 20, 9800, True, 1.0, "AG-LINE",
        (
            _p("Peak brake temperature", "°C", 210.0, 96.0, 9.0, 0.9, 40.0),
            _p("Wear-pin margin", "mm", 12.0, -10.0, 0.25, 0.0, 0.0, 0.0),
        ),
        hard_time_fh=1600.0,
    ),
    ComponentType(
        "LG-STR", "LG", "Shock strut", 3, 4200, "LDG-120", 50, 22000, True, 2.0, "AG-BASE",
        (
            _p("Strut pressure", "psi", 1650.0, -260.0, 20.0, 2.2, 15.0),
            _p("Static extension", "mm", 260.0, -36.0, 3.0, 0.08, -4.0),
        ),
    ),
    ComponentType(
        "LG-TYR", "LG", "Main wheel tyre", 2, 1100, "LDG-009", 7, 1800, False, 0.5, "AG-LINE",
        (
            _p("Tyre pressure", "psi", 200.0, -38.0, 2.5, 0.35, 0.0),
            _p("Tread depth", "mm", 9.0, -7.0, 0.2, 0.0, 0.0, 0.0),
        ),
        hard_time_fh=900.0, reorder_level=4,
    ),
    ComponentType(
        "AVN-FCC", "AVN", "Flight management computer", 5, 4400, "AVN-500", 55, 64000, True,
        1.5, "AG-DEPOT",
        (
            _p("Board temperature", "°C", 48.0, 22.0, 1.5, 0.45, 1.0),
            _p("Built-in-test warnings", "per flight", 0.02, 2.2, 0.08, 0.0, 0.0, 0.0),
        ),
    ),
    ComponentType(
        "AVN-DSP", "AVN", "Display unit", 2, 3900, "AVN-310", 25, 8800, True, 0.5, "AG-LINE",
        (
            _p("Backlight current", "mA", 410.0, 140.0, 9.0, 0.3),
            _p("Pixel fault count", "count", 0.5, 9.0, 0.4, 0.0, 0.0, 0.0),
        ),
    ),
    ComponentType(
        "AVN-SNS", "AVN", "Air-data sensor suite", 3, 3300, "AVN-145", 30, 15600, True, 1.0,
        "AG-BASE",
        (
            _p("Air-data bias", "%", 0.1, 2.4, 0.15, 0.003),
            _p("Probe heater current", "A", 3.2, -1.2, 0.08, -0.02),
        ),
    ),
    ComponentType(
        "FUE-BST", "FUEL", "Fuel boost pump", 4, 3000, "FUE-220", 32, 11200, True, 1.0, "AG-LINE",
        (
            _p("Discharge pressure", "psi", 28.0, -9.0, 0.7, -0.02, -1.0),
            _p("Motor current", "A", 7.5, 3.4, 0.25, 0.01, 0.6),
        ),
    ),
    ComponentType(
        "FUE-QTY", "FUEL", "Fuel quantity sensor", 2, 4600, "FUE-031", 18, 3100, False, 0.5,
        "AG-LINE",
        (_p("Quantity disagreement", "%", 0.4, 4.5, 0.25, 0.004, 0.0, 0.0),),
    ),
    ComponentType(
        "ECS-PCK", "ECS", "Cooling pack", 3, 2900, "ECS-410", 38, 19800, True, 2.0, "AG-BASE",
        (
            _p("Pack outlet temperature", "°C", 6.0, 17.0, 1.2, 0.32, 2.0),
            _p("Air-cycle machine speed", "krpm", 31.0, 4.5, 0.35, 0.05, 1.0),
        ),
    ),
    ComponentType(
        "ECS-PRC", "ECS", "Cabin pressure controller", 4, 3800, "ECS-220", 26, 9400, True, 1.0,
        "AG-LINE",
        (
            _p("Cabin pressure error", "hPa", 0.6, 6.5, 0.4, 0.004, 0.5, 0.0),
            _p("Outflow valve position", "%", 44.0, 18.0, 1.8, 0.15, 3.0),
        ),
    ),
)

# Project Forge (synthetic assumption): about 20 % of part numbers have an additive-manufacturing
# qualified replacement — the lower-criticality housing, filter, display and sensor items. A
# printable part with no stock is printed instead of ordered. History before the as-of date was
# generated without this capability; it applies to decisions and projections from as-of onward.
ADDITIVE_PRINTABLE = frozenset({"HYD-FLT", "AVN-DSP", "FUE-QTY", "ECS-PCK"})
PRINT_DAYS = 1  # print, post-process and inspect
COMPONENT_TYPES = tuple(
    replace(t, additive_printable=t.code in ADDITIVE_PRINTABLE) for t in COMPONENT_TYPES
)

TYPE_INDEX = {component_type.code: index for index, component_type in enumerate(COMPONENT_TYPES)}
SYSTEM_INDEX = {code: index for index, (code, _) in enumerate(SYSTEMS)}
SYSTEM_NAMES = dict(SYSTEMS)
AGENCY_INDEX = {agency.id: index for index, agency in enumerate(AGENCIES)}
MAX_PARAMETERS = max(len(component_type.parameters) for component_type in COMPONENT_TYPES)


def tail_code(index: int) -> str:
    return f"AC-{index + 1:03d}"
