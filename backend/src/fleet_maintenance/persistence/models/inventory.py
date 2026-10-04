from datetime import UTC, datetime

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from fleet_maintenance.persistence.database import Base


class Part(Base):
    __tablename__ = "parts"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    on_hand: Mapped[int] = mapped_column(Integer)
    lead_time_slots: Mapped[int] = mapped_column(Integer, default=0)
    version: Mapped[int] = mapped_column(Integer, default=1)


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = (UniqueConstraint("plan_id", "part_id", name="uq_plan_part_reservation"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    plan_id: Mapped[str] = mapped_column(ForeignKey("plans.id"), index=True)
    part_id: Mapped[str] = mapped_column(ForeignKey("parts.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(24), default="reserved")


class PartArrival(Base):
    __tablename__ = "part_arrivals"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    part_id: Mapped[str] = mapped_column(ForeignKey("parts.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    arrival_slot: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(24), default="expected")
    version: Mapped[int] = mapped_column(Integer, default=1)
    reason: Mapped[str] = mapped_column(String(1000))
    actor: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    received_at: Mapped[datetime | None] = mapped_column(nullable=True)
