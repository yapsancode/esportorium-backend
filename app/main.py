from fastapi import FastAPI

from app.core.config import get_settings
from app.core.database import create_db_and_tables

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()


@app.get("/health", tags=["health"])
def health_check() -> dict:
    return {"status": "ok"}
