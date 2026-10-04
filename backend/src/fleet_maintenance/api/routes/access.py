from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from fleet_maintenance.api.dependencies import Actor, current_actor
from fleet_maintenance.persistence.database import get_session
from fleet_maintenance.persistence.models import User
from fleet_maintenance.services.access import COOKIE_NAME, login, session_record
from fleet_maintenance.settings import get_settings

router = APIRouter(prefix="/access", tags=["access"])


class Credentials(BaseModel):
    user_id: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class SessionInfo(BaseModel):
    id: str
    role: str
    authentication: str
    csrf_token: str | None = None


@router.get("/session", response_model=SessionInfo)
def session(
    request: Request,
    actor: Actor = Depends(current_actor),
    database: Session = Depends(get_session),
) -> dict[str, object]:
    mode = get_settings().authentication_mode
    return {
        "id": actor.id,
        "role": actor.role,
        "authentication": "server session" if mode == "session" else "demonstration header",
        "csrf_token": session_record(database, request).csrf_token if mode == "session" else None,
    }


@router.post("/session", response_model=SessionInfo)
def create_session(
    credentials: Credentials,
    request: Request,
    response: Response,
    database: Session = Depends(get_session),
) -> dict[str, object]:
    settings = get_settings()
    if settings.authentication_mode != "session":
        raise HTTPException(404, "Session login is disabled in demonstration mode")
    if request.headers.get("origin") not in settings.allowed_origins:
        raise HTTPException(403, "Allowed request origin required")
    token, record = login(database, credentials.user_id, credentials.password)
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="strict",
        max_age=settings.session_hours * 3600,
        path=settings.api_prefix,
    )
    user = database.get(User, record.user_id)
    assert user is not None
    return {
        "id": record.user_id,
        "role": user.role,
        "authentication": "server session",
        "csrf_token": record.csrf_token,
    }


@router.delete("/session", status_code=204)
def logout(
    request: Request,
    response: Response,
    actor: Actor = Depends(current_actor),
    database: Session = Depends(get_session),
) -> None:
    del actor
    if get_settings().authentication_mode == "session":
        database.delete(session_record(database, request))
        database.commit()
    response.delete_cookie(COOKIE_NAME, path=get_settings().api_prefix)
