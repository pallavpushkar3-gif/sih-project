from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from fleet_maintenance.persistence.database import Base


class MaintenanceTask(Base):
    __tablename__ = "maintenance_tasks"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    component_id: Mapped[str] = mapped_column(ForeignKey("components.id"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    duration_slots: Mapped[int] = mapped_column(Integer)
    earliest_slot: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    deadline_slot: Mapped[int] = mapped_column(Integer)
    required_skill: Mapped[str] = mapped_column(String(64))
    required_part_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    required_part_quantity: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    fixed_start: Mapped[int | None] = mapped_column(nullable=True)
    predecessors: Mapped[list[str]] = mapped_column(JSON, default=list, server_default="[]")
    grouping_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(32), default="open")
    version: Mapped[int] = mapped_column(Integer, default=1)


class Plan(Base):
    __tablename__ = "plans"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(32))
    solver_status: Mapped[str] = mapped_column(String(32))
    input_version: Mapped[str] = mapped_column(String(128))
    input_snapshot: Mapped[dict[str, object]] = mapped_column(
        JSON, default=dict, server_default="{}"
    )
    objective: Mapped[float | None] = mapped_column(nullable=True)
    best_bound: Mapped[float | None] = mapped_column(nullable=True)
    parent_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    assignments: Mapped[list[dict[str, object]]] = mapped_column(
        JSON, default=list, server_default="[]"
    )
    diagnostics: Mapped[list[str]] = mapped_column(JSON, default=list, server_default="[]")
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    approved_at: Mapped[datetime | None] = mapped_column(nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
