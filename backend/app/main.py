"""Main FastAPI Application Entrypoint.

MCP-Based Multi-Agent Framework for Autonomous Scientific Literature Review
and Research Gap Assessment (Phase 1).
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.services.persistence.database import init_db
from backend.app.api.routes import research, strategy, search, papers, exports, mcp_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event handler for database initialization and cleanup."""
    logger.info(f"Starting {settings.APP_NAME} (v{settings.APP_VERSION}) in {settings.APP_ENV} mode...")
    init_db()
    logger.info("Application startup sequence complete.")
    yield
    logger.info("Application shutdown completed.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Autonomous academic literature retrieval and research gap assessment system. "
        "Provides multi-provider search (OpenAlex, Semantic Scholar, Crossref, arXiv), "
        "reproducible query strategy generation, canonical metadata normalization, "
        "hierarchical deduplication, and Model Context Protocol (MCP) tool exposure."
    ),
    lifespan=lifespan,
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(research.router)
app.include_router(strategy.router)
app.include_router(search.router)
app.include_router(papers.router)
app.include_router(exports.router)
app.include_router(mcp_routes.router)


@app.get("/api/health", tags=["Health"])
def health_check():
    """Health probe endpoint."""
    return {
        "status": "healthy",
        "system": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "phase": "Phase 1: Research Input, Search Strategy & Literature Retrieval",
    }


# Mount built frontend static files if available
frontend_dist_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")
if os.path.exists(frontend_dist_path):
    app.mount("/", StaticFiles(directory=frontend_dist_path, html=True), name="frontend")
else:
    @app.get("/", tags=["Health"])
    def root_status():
        return {
            "status": "online",
            "system": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "phase": "Phase 1: Research Input, Search Strategy & Literature Retrieval",
            "docs_url": "/docs",
            "mcp_tools_url": "/api/mcp/tools",
        }


