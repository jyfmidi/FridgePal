"""Fridgital FastAPI application entry point."""

import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.health import router as health_router
from app.api.inventory import build_inventory_router
from app.config import get_settings
from app.infrastructure.db import models as _models  # noqa: F401
from app.infrastructure.db.demo_seed import seed_demo_inventory
from app.infrastructure.db.session import create_database, session_dependency

APP_VERSION = "0.1.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


def create_app() -> FastAPI:
    """Build the FastAPI application."""
    settings = get_settings()
    engine, session_factory = create_database(settings.database_url)
    if settings.seed_demo_data:
        seed_demo_inventory(session_factory)

    def get_session():
        yield from session_dependency(session_factory)

    app = FastAPI(title="Fridgital", version=APP_VERSION)
    app.include_router(health_router, prefix="/api")
    app.include_router(build_inventory_router(get_session), prefix="/api")
    app.state.database_engine = engine

    static_dir = os.environ.get("STATIC_DIR", "static")
    static_path = Path(static_dir)
    if static_path.is_dir() and (static_path / "index.html").is_file():
        # Serve the built frontend; /api routes above keep precedence.
        app.mount("/", StaticFiles(directory=static_path, html=True), name="static")

    return app


app = create_app()
