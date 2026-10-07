from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from fleet_maintenance.persistence.database import get_session
from fleet_maintenance.services.access import authenticate_session
from fleet_maintenance.settings import get_settings


@dataclass(frozen=True)
class Actor:
    id: str
    role: str


def current_actor(
    request: Request,
    session: Session = Depends(get_session),
    x_demo_user: str = Header(default="demo-planner"),
    x_demo_role: str = Header(default="planner"),
) -> Actor:
    if get_settings().authentication_mode == "session":
        user = authenticate_session(session, request)
        return Actor(user.id, user.role)
    if x_demo_role not in {
        "viewer",
        "fleet_manager",
        "planner",
        "engineer",
        "logistics",
        "supervisor",
        "administrator",
    }:
        raise HTTPException(403, "Unknown demonstration role")
    return Actor(x_demo_user, x_demo_role)


def require_planner(actor: Actor) -> Actor:
    if actor.role not in {"planner", "supervisor"}:
        raise HTTPException(403, "Planner or supervisor role required")
    return actor


def require_engineer(actor: Actor) -> Actor:
    if actor.role not in {"engineer", "supervisor"}:
        raise HTTPException(403, "Engineer or supervisor role required")
    return actor


def require_supervisor(actor: Actor) -> Actor:
    if actor.role != "supervisor":
        raise HTTPException(403, "Supervisor role required")
    return actor
