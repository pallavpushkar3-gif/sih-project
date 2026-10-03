from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fleet_maintenance.api.router import router
from fleet_maintenance.persistence.database import SessionLocal, create_schema
from fleet_maintenance.services.records import seed_demo
from fleet_maintenance.settings import get_settings


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    settings.artifact_root.mkdir(parents=True, exist_ok=True)
    if settings.auto_create_schema:
        create_schema()
    if settings.auto_seed_demo:
        with SessionLocal() as session:
            seed_demo(session)
    yield


app = FastAPI(title="Fleet Maintenance Decision API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix=get_settings().api_prefix)
