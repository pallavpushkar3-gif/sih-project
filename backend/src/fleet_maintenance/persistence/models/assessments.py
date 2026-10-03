from datetime import UTC, datetime

from sqlalchemy import JSON, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from fleet_maintenance.persistence.database import Base


class Assessment(Base):
    __tablename__ = "assessments"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    component_id: Mapped[str] = mapped_column(ForeignKey("components.id"), index=True)
    state: Mapped[str] = mapped_column(String(32))
    estimate_cycles: Mapped[float | None] = mapped_column(Float, nullable=True)
    lower_cycles: Mapped[float | None] = mapped_column(Float, nullable=True)
    upper_cycles: Mapped[float | None] = mapped_column(Float, nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(80), nullable=True)
    input_version: Mapped[str] = mapped_column(String(120))
    quality_findings: Mapped[list[dict[str, str]]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    component_id: Mapped[str] = mapped_column(ForeignKey("components.id"), index=True)
    state: Mapped[str] = mapped_column(String(32))
    reason: Mapped[str] = mapped_column(String(240))
    policy_version: Mapped[str] = mapped_column(String(64))
    assessment_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    acknowledged_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
