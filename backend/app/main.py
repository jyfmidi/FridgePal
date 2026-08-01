"""Fridge Pal FastAPI application entry point."""

import logging
import os
from pathlib import Path, PurePosixPath

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Scope

from app.api.admin import build_admin_router
from app.api.auth import build_auth_router
from app.api.health import router as health_router
from app.api.history import build_history_router
from app.api.inventory import build_inventory_router
from app.api.recipes import build_recipe_router
from app.api.rescue import build_rescue_router
from app.application.admin.service import ensure_default_settings
from app.auth.dependencies import current_user_factory
from app.auth.password import hash_password
from app.auth.service import create_user
from app.config import get_settings, validate_auth_settings
from app.infrastructure.db import models as _models  # noqa: F401
from app.infrastructure.db.demo_seed import (
    normalize_legacy_inventory_units,
    seed_demo_inventory_for_user,
)
from app.infrastructure.db.session import create_database, session_dependency
from app.infrastructure.recipe.factory import build_recipe_adapters

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
    problems = validate_auth_settings(settings)
    if problems:
        raise RuntimeError(
            "Invalid auth configuration: "
            + "; ".join(problems)
            + " (public deployments must set these values; see .env.example)"
        )
    engine, session_factory = create_database(settings.database_url)
    normalize_legacy_inventory_units(session_factory)

    # Create the built-in demo account and seed its data (only when demo seeding
    # is enabled; registered users inherit the same gate via seed_on_register).
    current_user = current_user_factory(session_factory)
    if settings.seed_demo_data:
        with session_factory() as session:
            from sqlalchemy import select as _select

            from app.infrastructure.db.models import UserRow

            demo_user = session.scalar(_select(UserRow).where(UserRow.username == "demo"))
            if demo_user is None:
                demo_user = create_user(
                    session,
                    "demo",
                    settings.demo_password,
                    is_demo=True,
                )
                seed_demo_inventory_for_user(session_factory, demo_user.id)

    # Provision the fixed administrator account (FRIDGE_PAL_ADMIN_USERNAME /
    # FRIDGE_PAL_ADMIN_PASSWORD). The .env values are the source of truth and
    # are re-synced on every boot, so the operator can rotate the password by
    # editing configuration and restarting. The admin owns no kitchen data.
    with session_factory() as session:
        from sqlalchemy import select as _select

        from app.infrastructure.db.models import UserRow

        admin_user = session.scalar(
            _select(UserRow).where(UserRow.username == settings.admin_username)
        )
        if admin_user is None:
            create_user(
                session,
                settings.admin_username,
                settings.admin_password,
                is_admin=True,
            )
        else:
            if not admin_user.is_admin:
                raise RuntimeError(
                    f"FRIDGE_PAL_ADMIN_USERNAME ({settings.admin_username}) is taken by a "
                    "non-admin user; choose another admin username"
                )
            admin_user.password_hash = hash_password(settings.admin_password)
            session.commit()
        ensure_default_settings(session)

    def get_session():
        yield from session_dependency(session_factory)

    app = FastAPI(title="Fridge Pal", version=APP_VERSION)

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return response

    app.include_router(health_router, prefix="/api")
    app.include_router(
        build_auth_router(
            get_session,
            session_factory,
            current_user,
            seed_on_register=settings.seed_demo_data,
        ),
        prefix="/api",
    )
    app.include_router(build_inventory_router(get_session, current_user), prefix="/api")
    app.include_router(build_admin_router(get_session, current_user), prefix="/api")
    try:
        recipe_adapters = build_recipe_adapters(settings)
        app.include_router(
            build_rescue_router(get_session, recipe_adapters, current_user),
            prefix="/api",
        )
    except ValueError:
        logging.getLogger(__name__).warning("Recipe adapters unavailable; rescue search disabled.")
    app.include_router(build_recipe_router(get_session, current_user), prefix="/api")
    app.include_router(build_history_router(get_session, current_user), prefix="/api")
    app.state.database_engine = engine

    static_dir = os.environ.get("STATIC_DIR", "static")
    static_path = Path(static_dir)
    if static_path.is_dir() and (static_path / "index.html").is_file():
        # Serve the built frontend; /api routes above keep precedence.
        app.mount("/", SPAStaticFiles(directory=static_path, html=True), name="static")

    return app


app = create_app()
