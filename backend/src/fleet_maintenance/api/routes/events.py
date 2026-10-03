import asyncio
import json
from collections.abc import AsyncIterator, Callable

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from fleet_maintenance.api.dependencies import Actor, current_actor
from fleet_maintenance.persistence.database import SessionLocal
from fleet_maintenance.persistence.models import OutboxEvent

router = APIRouter(prefix="/events", tags=["events"])
SessionFactory = Callable[[], Session]


def encode_event(event: OutboxEvent) -> str:
    envelope = {
        "event_id": event.id,
        "type": event.payload.get("event_type", event.topic),
        "occurred_at": event.created_at.isoformat(),
        "payload": event.payload,
    }
    return (
        f"id: {event.id}\n"
        f"event: {envelope['type']}\n"
        f"data: {json.dumps(envelope, separators=(',', ':'))}\n\n"
    )


def published_after(
    cursor: int, limit: int = 100, session_factory: SessionFactory = SessionLocal
) -> list[OutboxEvent]:
    with session_factory() as session:
        return list(
            session.scalars(
                select(OutboxEvent)
                .where(
                    OutboxEvent.id > cursor,
                    OutboxEvent.published_at.is_not(None),
                )
                .order_by(OutboxEvent.id)
                .limit(limit)
            ).all()
        )


@router.get("")
async def events(
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    _: Actor = Depends(current_actor),
) -> StreamingResponse:
    try:
        initial_cursor = int(last_event_id) if last_event_id else 0
    except ValueError as exc:
        raise HTTPException(422, "Last-Event-ID must be an integer") from exc
    if initial_cursor < 0:
        raise HTTPException(422, "Last-Event-ID must be nonnegative")

    async def stream() -> AsyncIterator[str]:
        cursor = initial_cursor
        yield f"event: connected\ndata: {json.dumps({'status': 'connected', 'cursor': cursor})}\n\n"
        heartbeat = 0
        while True:
            rows = published_after(cursor)
            for row in rows:
                yield encode_event(row)
                cursor = row.id
            heartbeat += 1
            if heartbeat >= 30:
                yield ": keepalive\n\n"
                heartbeat = 0
            await asyncio.sleep(0.5)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
