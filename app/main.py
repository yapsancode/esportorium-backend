from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.brackets import router as brackets_router
from app.api.disputes import router as disputes_router
from app.api.games import router as games_router
from app.api.matches import router as matches_router
from app.api.registrations import router as registrations_router
from app.api.tournaments import router as tournaments_router
from app.api.users import router as users_router
from app.core.config import get_settings
from app.core.database import create_db_and_tables

# Import all models so SQLModel's metadata is populated before create_db_and_tables().
import app.models.dispute  # noqa: F401
import app.models.draft  # noqa: F401
import app.models.game  # noqa: F401
import app.models.match  # noqa: F401
import app.models.registration  # noqa: F401
import app.models.team  # noqa: F401
import app.models.tournament  # noqa: F401
import app.models.user  # noqa: F401

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(tournaments_router)
app.include_router(registrations_router)
app.include_router(brackets_router)
app.include_router(matches_router)
app.include_router(disputes_router)
app.include_router(games_router)


@app.get("/health", tags=["health"])
def health_check() -> dict:
    return {"status": "ok"}
