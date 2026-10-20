import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from apps.api.app.config import get_settings
from apps.api.app.db.session import close_pool, run_migrations
from apps.api.app.errors import register_error_handlers
from apps.api.app.logging import get_logger, request_id_var, setup_logging
from apps.api.app.routes import api_router
from apps.api.app.routes.health import run_all_self_checks

setup_logging()
logger = get_logger("apps.api.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info(f"Starting AskQuiz.IQ API on {settings.PUBLIC_API_URL}")

    # Run database migrations
    try:
        run_migrations()
        logger.info("Database migrations complete")
    except Exception as exc:
        logger.error(f"Failed to apply database migrations at startup: {exc}")

    # Run self-check
    try:
        check_results = run_all_self_checks()
        if check_results["status"] == "ok":
            logger.info("Startup self-check passed: all systems operational")
        else:
            logger.warning(f"Startup self-check degraded: {check_results['checks']}")
    except Exception as exc:
        logger.error(f"Error during startup self-check: {exc}")

    yield

    logger.info("Shutting down AskQuiz.IQ API...")
    close_pool()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="AskQuiz.IQ API",
        version="0.1.0",
        description="Pause & Ask Learning Assistant API",
        lifespan=lifespan,
    )

    # Middleware: Request ID injection
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = request_id_var.set(req_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = req_id
            return response
        finally:
            request_id_var.reset(token)

    # CORS configuration
    origins = settings.allowed_origins_list
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if origins else ["*"],
        allow_origin_regex=r"https://.*\.trycloudflare\.com",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register error handlers
    register_error_handlers(app)

    # Mount API routes
    app.include_router(api_router)
    from apps.api.app.routes.videos import router as videos_router
    app.include_router(videos_router)
    from apps.api.app.routes.ask import router as ask_router
    app.include_router(ask_router)

    return app


app = create_app()
