from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from fleet_maintenance.persistence import models  # noqa: F401
from fleet_maintenance.persistence.database import Base
from fleet_maintenance.services.records import seed_demo


@pytest.fixture
def isolated_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        seed_demo(session)
        yield session
    engine.dispose()
