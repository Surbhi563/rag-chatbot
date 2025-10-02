"""Main FastAPI application for RAG chatbot."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.middleware import LoggingMiddleware, SecurityHeadersMiddleware
from app.api.routes_taxonomy import router as taxonomy_router
from app.api.routes_uploads import router as uploads_router
from app.api.routes_chat import router as chat_router
from app.api.routes_websites import router as websites_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger


configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("starting rag-chatbot", version=settings.app_version, env=settings.env)
    yield
    logger.info("shutting down rag-chatbot")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="RAG Chatbot - Ask questions about your documents",
        docs_url="/docs",
        redoc_url=None,
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(LoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(uploads_router)
    app.include_router(taxonomy_router)
    app.include_router(chat_router)
    app.include_router(websites_router)

    @app.get("/health")
    async def health() -> JSONResponse:
        return JSONResponse(content={"ok": True})

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, reload=settings.is_dev)