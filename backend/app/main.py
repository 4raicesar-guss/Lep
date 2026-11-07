from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    analytics_router,
    auth_router,
    buildings_router,
    combat_router,
    formation_router,
    health_router,
    player_router,
    resources_router,
    units_router,
)
from app.db.base import Base
from app.db.database import engine
import app.db.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="Granja Táctica API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(analytics_router)
app.include_router(combat_router)
app.include_router(player_router)
app.include_router(units_router)
app.include_router(resources_router)
app.include_router(formation_router)
app.include_router(buildings_router)

