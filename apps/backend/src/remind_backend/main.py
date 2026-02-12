"""FastAPI backend server for Remind."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from remind_backend.api.v1.router import api_router
from remind_backend.config import get_settings
from remind_backend.logging import setup_logging
from remind_backend.middleware import (
    GlobalRateLimitMiddleware,
    ErrorTrackingMiddleware,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    from remind_backend.database import Base, get_engine

    Base.metadata.create_all(get_engine())
    yield


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    setup_logging(debug=settings.debug)

    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        lifespan=lifespan,
    )

    app.add_middleware(ErrorTrackingMiddleware)
    app.add_middleware(GlobalRateLimitMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health")
    def health():
        """Health check endpoint."""
        return {"status": "ok", "version": settings.api_version}

    @app.exception_handler(Exception)
    async def exception_handler(request, exc):
        """Global exception handler."""
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)},
        )

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "remind_backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
