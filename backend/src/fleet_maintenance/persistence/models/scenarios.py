from sqlalchemy import JSON, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from fleet_maintenance.persistence.database import Base


class Scenario(Base):
    __tablename__ = "scenarios"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    version: Mapped[int] = mapped_column(default=1)
    assumptions: Mapped[dict[str, object]] = mapped_column(JSON)
    provenance: Mapped[str] = mapped_column(String(32), default="synthetic")


class SimulationRun(Base):
    __tablename__ = "simulation_runs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(String(64), index=True)
    policy: Mapped[str] = mapped_column(String(64))
    seed: Mapped[int] = mapped_column()
    availability: Mapped[float] = mapped_column(Float)
    metrics: Mapped[dict[str, object]] = mapped_column(JSON)
