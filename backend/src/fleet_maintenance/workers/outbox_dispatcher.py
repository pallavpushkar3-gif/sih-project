import time
from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from fleet_maintenance.persistence.database import SessionLocal
from fleet_maintenance.persistence.models import OutboxEvent
from fleet_maintenance.settings import get_settings
from fleet_maintenance.workers.celery_app import app

Publisher = Callable[[OutboxEvent], None]
SessionFactory = Callable[[], Session]


def publish_to_broker(event: OutboxEvent) -> None:
    event_type = str(event.payload.get("event_type", ""))
    if event_type == "job.queued":
        app.send_task("jobs.execute", args=[event.payload["job_id"]])
    else:
        app.send_task("events.observe", args=[event.payload])


def dispatch_one(session_factory: SessionFactory, publish: Publisher) -> bool:
    with session_factory() as session:
        event = session.scalar(
            select(OutboxEvent)
            .where(OutboxEvent.published_at.is_(None))
            .order_by(OutboxEvent.id)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if event is None:
            return False
        publish(event)
        event.published_at = datetime.now(UTC)
        session.commit()
        return True


def dispatch_batch(
    session_factory: SessionFactory, publish: Publisher, *, limit: int
) -> int:
    dispatched = 0
    for _ in range(limit):
        if not dispatch_one(session_factory, publish):
            break
        dispatched += 1
    return dispatched


def main() -> None:
    settings = get_settings()
    while True:
        dispatched = dispatch_batch(
            SessionLocal, publish_to_broker, limit=settings.outbox_batch_size
        )
        if dispatched == 0:
            time.sleep(settings.outbox_poll_seconds)


if __name__ == "__main__":
    main()
