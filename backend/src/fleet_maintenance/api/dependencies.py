from dataclasses import dataclass

from fastapi import Header, HTTPException


@dataclass(frozen=True)
class Actor:
    id: str
    role: str


def current_actor(
    x_demo_user: str = Header(default="demo-planner"),
    x_demo_role: str = Header(default="planner"),
) -> Actor:
    if x_demo_role not in {"viewer", "planner", "engineer", "logistics", "supervisor"}:
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
