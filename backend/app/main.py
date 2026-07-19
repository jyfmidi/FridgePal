"""Fridge Pal FastAPI application entry point."""

import logging
import os
from pathlib import Path, PurePosixPath

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from starlette.responses import Response
from starlette.types import Scope

from app.api.health import router as health_router
from app.api.inventory import build_inventory_router
from app.config import get_settings
from app.infrastructure.db import models as _models  # noqa: F401
from app.infrastructure.db.demo_seed import normalize_legacy_inventory_units, seed_demo_inventory
from app.infrastructure.db.session import create_database, session_dependency

APP_VERSION = "0.1.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


class SPAStaticFiles(StaticFiles):
    """Serve Vue history routes from index.html while preserving missing-asset 404s."""

    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            if exc.status_code != 404 or PurePosixPath(path).suffix:
                raise
            return await super().get_response("index.html", scope)


def create_app() -> FastAPI:
    """Build the FastAPI application."""
    settings = get_settings()
    engine, session_factory = create_database(settings.database_url)
    normalize_legacy_inventory_units(session_factory)
    if settings.seed_demo_data:
        seed_demo_inventory(session_factory)

    def get_session():
        yield from session_dependency(session_factory)

    app = FastAPI(title="Fridge Pal", version=APP_VERSION)
    app.include_router(health_router, prefix="/api")
    app.include_router(build_inventory_router(get_session), prefix="/api")
    app.state.database_engine = engine

    static_dir = os.environ.get("STATIC_DIR", "static")
    static_path = Path(static_dir)
    if static_path.is_dir() and (static_path / "index.html").is_file():
        # Serve the built frontend; /api routes above keep precedence.
        app.mount("/", SPAStaticFiles(directory=static_path, html=True), name="static")

    return app


app = create_app()
