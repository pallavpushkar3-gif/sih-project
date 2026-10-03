from datetime import UTC, datetime

from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from fleet_maintenance.persistence.database import Base


class Aircraft(Base):
    __tablename__ = "aircraft"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tail_number: Mapped[str] = mapped_column(String(64), unique=True)
    label: Mapped[str] = mapped_column(String(120))
    provenance: Mapped[str] = mapped_column(String(32), default="synthetic")


class Component(Base):
    __tablename__ = "components"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    aircraft_id: Mapped[str] = mapped_column(ForeignKey("aircraft.id"), index=True)
    serial_number: Mapped[str] = mapped_column(String(80), unique=True)
    kind: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(32), default="monitoring")
    current_cycle: Mapped[int] = mapped_column(Integer, default=0)


class Observation(Base):
    __tablename__ = "observations"
    __table_args__ = (UniqueConstraint("component_id", "cycle", "sensor", name="uq_observation"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    component_id: Mapped[str] = mapped_column(ForeignKey("components.id"), index=True)
    cycle: Mapped[int] = mapped_column(Integer)
    sensor: Mapped[str] = mapped_column(String(40))
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(24))
    source_version: Mapped[str] = mapped_column(String(80))
    observed_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
