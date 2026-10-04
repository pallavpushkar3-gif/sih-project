import asyncio
import json
from collections.abc import AsyncIterator, Callable

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from fleet_maintenance.api.dependencies import Actor, current_actor
from fleet_maintenance.persistence.database import SessionLocal, get_session
from fleet_maintenance.persistence.models import OutboxEvent
from fleet_maintenance.services.access import authenticate_session
from fleet_maintenance.settings import get_settings

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
        rows = session.scalars(
            select(OutboxEvent).where(OutboxEvent.id > cursor).order_by(OutboxEvent.id).limit(limit)
        ).all()
        confirmed = []
        for row in rows:
            if row.published_at is None:
                break  # Never move a client cursor past a pending lower-ID publication.
            confirmed.append(row)
        return confirmed


def replay_position(
    cursor: int, session_factory: SessionFactory = SessionLocal
) -> tuple[int, str | None]:
    with session_factory() as session:
        oldest, latest = session.execute(
            select(func.min(OutboxEvent.id), func.max(OutboxEvent.id))
        ).one()
    if cursor and latest is None:
        return 0, "history_unavailable"
    if latest is not None and cursor > latest:
        return 0, "cursor_ahead_of_history"
    if oldest is not None and cursor and cursor < oldest - 1:
        return oldest - 1, "history_gap"
    return cursor, None


def stream_authorized(request: Request, session_factory: SessionFactory = SessionLocal) -> bool:
    if get_settings().authentication_mode == "demo":
        return True
    with session_factory() as session:
        try:
            authenticate_session(session, request)
        except HTTPException:
            return False
    return True


@router.get("")
async def events(
    request: Request,
    session: Session = Depends(get_session),
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    _: Actor = Depends(current_actor),
) -> StreamingResponse:
    try:
        initial_cursor = int(last_event_id) if last_event_id else 0
    except ValueError as exc:
        raise HTTPException(422, "Last-Event-ID must be an integer") from exc
    if initial_cursor < 0:
        raise HTTPException(422, "Last-Event-ID must be nonnegative")

    session.rollback()  # Release the authentication read transaction before streaming.

    async def stream() -> AsyncIterator[str]:
        cursor = initial_cursor
        yield f"event: connected\ndata: {json.dumps({'status': 'connected', 'cursor': cursor})}\n\n"
        heartbeat = 0
        while True:
            if heartbeat % 30 == 0 and not await asyncio.to_thread(stream_authorized, request):
                yield 'event: auth.required\ndata: {"reason":"session_expired_or_revoked"}\n\n'
                return
            position, reason = await asyncio.to_thread(replay_position, cursor)
            if reason:
                cursor = position
                message = json.dumps({"reason": reason, "refresh_authoritative_state": True})
                yield (f"id: {cursor}\nevent: resync\ndata: {message}\n\n")
            rows = await asyncio.to_thread(published_after, cursor)
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
