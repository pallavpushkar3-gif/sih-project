from collections.abc import Generator
from datetime import datetime

from sqlalchemy import DateTime, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from fleet_maintenance.settings import get_settings


class Base(DeclarativeBase):
    type_annotation_map = {datetime: DateTime(timezone=True)}


def _engine_kwargs(url: str) -> dict[str, object]:
    return {"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {}


settings = get_settings()
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    hide_parameters=True,
    **_engine_kwargs(settings.database_url),
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session


def create_schema() -> None:
    from fleet_maintenance.persistence import models  # noqa: F401

    Base.metadata.create_all(engine)
