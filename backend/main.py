"""BacktestPro — FastAPI application entry point.

Configures CORS, registers routers, sets up WebSocket endpoint,
initializes the database, and handles global exception formatting.
"""

import json
import logging
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import settings
from core.exceptions import BacktestProException
from models.database import init_db
from routers import auth, backtest, data, reports, strategies

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("backtestpro")


# =========================================================
# APPLICATION LIFESPAN
# =========================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("🚀 BacktestPro starting up...")
    logger.info(f"   Auth enabled: {settings.auth_enabled}")
    logger.info(f"   Database: {settings.database_url}")
    logger.info(f"   Cache dir: {settings.cache_dir}")

    # Initialize database tables
    await init_db()
    logger.info("   ✅ Database initialized")

    yield

    logger.info("👋 BacktestPro shutting down...")


# =========================================================
# FASTAPI APP
# =========================================================
app = FastAPI(
    title="BacktestPro API",
    description="API de backtesting de estrategias de trading — Datos reales, ejecución local.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# =========================================================
# CORS MIDDLEWARE
# =========================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# GLOBAL EXCEPTION HANDLER
# =========================================================
@app.exception_handler(BacktestProException)
async def backtestpro_exception_handler(request: Request, exc: BacktestProException):
    """Format all BacktestPro exceptions into the standard error response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all for unexpected errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Error inesperado del servidor.",
                "details": {"exception": str(exc)},
            }
        },
    )


# =========================================================
# REGISTER ROUTERS
# =========================================================
app.include_router(data.router)
app.include_router(backtest.router)
app.include_router(strategies.router)
app.include_router(reports.router)
app.include_router(auth.router)


# =========================================================
# HEALTH CHECK
# =========================================================
@app.get("/health", tags=["system"])
async def health_check():
    """Health check endpoint for Docker healthcheck and monitoring."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "auth_enabled": settings.auth_enabled,
    }


# =========================================================
# WEBSOCKET — BACKTEST PROGRESS
# =========================================================
from core.state import active_ws_connections

@app.websocket("/ws/backtest/{job_id}")
async def websocket_backtest(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time backtest progress updates.

    Protocol:
    - Server sends JSON events: connected, started, progress, completed, failed, cancelled
    - Client is receive-only (does not send messages)

    Full implementation in FASE 2 (TASK-205).
    """
    await websocket.accept()

    # Register the connection
    if job_id not in active_ws_connections:
        active_ws_connections[job_id] = []
    active_ws_connections[job_id].append(websocket)

    try:
        # Send connected event
        await websocket.send_json({
            "event": "connected",
            "job_id": job_id,
            "status": "queued",
            "timestamp": "",
        })

        # Keep connection alive until client disconnects
        while True:
            # We only receive to detect disconnection; client doesn't send data
            await websocket.receive_text()

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for job {job_id}")
    finally:
        # Clean up connection
        if job_id in active_ws_connections:
            active_ws_connections[job_id] = [
                ws for ws in active_ws_connections[job_id] if ws != websocket
            ]
            if not active_ws_connections[job_id]:
                del active_ws_connections[job_id]


# =========================================================
# MAIN ENTRY POINT
# =========================================================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
    )
