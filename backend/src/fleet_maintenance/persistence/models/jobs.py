from datetime import UTC, datetime

from sqlalchemy import JSON, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from fleet_maintenance.persistence.database import Base


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    kind: Mapped[str] = mapped_column(String(48))
    state: Mapped[str] = mapped_column(String(32), default="queued")
    attempt: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    owner: Mapped[str] = mapped_column(
        String(64), default="demo-planner", server_default="demo-planner"
    )
    lease_expires_at: Mapped[datetime | None] = mapped_column(nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)
    input_payload: Mapped[dict[str, object]] = mapped_column(
        JSON, default=dict, server_default="{}"
    )
    result_payload: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))


class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    topic: Mapped[str] = mapped_column(String(80))
    payload: Mapped[dict[str, object]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)


class JobAttempt(Base):
    __tablename__ = "job_attempts"
    __table_args__ = (UniqueConstraint("job_id", "number", name="uq_job_attempt_number"),)
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), index=True)
    number: Mapped[int] = mapped_column(Integer)
    worker_id: Mapped[str] = mapped_column(String(240))
    state: Mapped[str] = mapped_column(String(32))
    started_at: Mapped[datetime] = mapped_column()
    lease_expires_at: Mapped[datetime] = mapped_column()
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)
    outcome_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
