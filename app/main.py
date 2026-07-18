"""FastAPI application factory and ASGI entry point."""

from __future__ import annotations

import asyncio
import os

from fastapi import FastAPI

from app.api.errors import ApiError, api_error_handler, unhandled_exception_handler
from app.api.middleware import RequestContextMiddleware
from app.api.openapi import openapi_tag_metadata
from app.config import Settings, get_settings
from app.lifespan import DatabaseFactory, create_lifespan, default_database_factory
from app.logging import configure_logging
from app.observability.health import router as health_router
from app.ovirt.mount import mount_ovirt_routes
from app.web.routes import router as web_router


def create_app(
    settings: Settings | None = None,
    database_factory: DatabaseFactory = default_database_factory,
) -> FastAPI:
    """Create an isolated application instance."""

    resolved = settings or get_settings()
    configure_logging(resolved.log_level)
    app = FastAPI(
        title=resolved.app_name,
        version="0.1.0",
        openapi_tags=openapi_tag_metadata(),
        lifespan=create_lifespan(resolved, database_factory, ()),
    )
    app.state.settings = resolved
    app.state.contract_swap_lock = asyncio.Lock()
    app.add_middleware(RequestContextMiddleware, header_name=resolved.request_id_header)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    app.add_exception_handler(ApiError, api_error_handler)
    app.include_router(web_router)
    app.include_router(health_router)
    mount_ovirt_routes(app, series=os.environ.get("OVIRT_SERIES", "4.5"))
    return app


app = create_app()
