"""Resource history plus database-enforced exclusive per-unit slot ownership."""

from sqlalchemy import JSON, CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from fleet_maintenance.persistence.database import Base


class MaintenanceResource(Base):
    __tablename__ = "maintenance_resources"
    __table_args__ = (
        CheckConstraint("capacity > 0", name="ck_resource_capacity"),
        CheckConstraint("valid_until > valid_from", name="ck_resource_validity"),
        CheckConstraint("kind IN ('crew', 'bay')", name="ck_resource_kind"),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    kind: Mapped[str] = mapped_column(String(16))
    label: Mapped[str] = mapped_column(String(160))
    capabilities: Mapped[list[str]] = mapped_column(JSON)
    available: Mapped[list[list[int]]] = mapped_column(JSON)
    aircraft_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    capacity: Mapped[int] = mapped_column(default=1)
    valid_from: Mapped[int] = mapped_column(default=0)
    valid_until: Mapped[int] = mapped_column(default=14)
    version: Mapped[int] = mapped_column(default=1)
    scope_component_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class ResourceBooking(Base):
    __tablename__ = "resource_bookings"
    __table_args__ = (
        UniqueConstraint("plan_id", "task_id", "resource_id", name="uq_resource_booking"),
        CheckConstraint("end_slot > start_slot", name="ck_booking_interval"),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    plan_id: Mapped[str] = mapped_column(ForeignKey("plans.id"))
    task_id: Mapped[str] = mapped_column(ForeignKey("maintenance_tasks.id"))
    resource_id: Mapped[str] = mapped_column(ForeignKey("maintenance_resources.id"))
    unit: Mapped[int]
    start_slot: Mapped[int]
    end_slot: Mapped[int]
    status: Mapped[str] = mapped_column(String(24), default="reserved")


class ResourceSlot(Base):
    __tablename__ = "resource_slots"
    __table_args__ = (
        UniqueConstraint("resource_id", "unit", "slot", name="uq_resource_unit_slot"),
        CheckConstraint("unit >= 0 AND slot >= 0", name="ck_resource_slot_positive"),
    )
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    resource_id: Mapped[str] = mapped_column(ForeignKey("maintenance_resources.id"))
    booking_id: Mapped[str] = mapped_column(ForeignKey("resource_bookings.id"))
    unit: Mapped[int]
    slot: Mapped[int]
