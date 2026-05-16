"""Backtest router — endpoints for running, monitoring, and managing backtests."""

import asyncio
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from models.schemas import BacktestRunRequest, BacktestFullResponse, BacktestHistoryResponse
from services.backtest_engine import backtest_engine
from services.data_manager import data_manager
from core.state import active_ws_connections, jobs_db

logger = logging.getLogger("backtestpro.routers.backtest")

router = APIRouter(prefix="/api/v1/backtest", tags=["backtest"])

async def notify_ws(job_id: str, payload: dict):
    """Send a JSON payload to all active websocket connections for a job."""
    if job_id in active_ws_connections:
        websockets = active_ws_connections[job_id]
        for ws in websockets:
            try:
                await ws.send_json(payload)
            except Exception as e:
                logger.error(f"Error sending WS message to {job_id}: {e}")

async def run_backtest_task(job_id: str, request: BacktestRunRequest):
    """Background task to fetch data, run backtest, and notify progress."""
    logger.info(f"Starting backtest task {job_id}")
    jobs_db[job_id]["status"] = "running"
    
    await notify_ws(job_id, {
        "event": "started",
        "job_id": job_id,
        "status": "running",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    try:
        # 1. Fetch Data
        await notify_ws(job_id, {"event": "progress", "job_id": job_id, "progress": 10, "message": "Descargando datos..."})
        ohlcv_result = await data_manager.get_ohlcv(
            symbol=request.symbol,
            timeframe=request.timeframe,
            start=request.start,
            end=request.end
        )
        
        if ohlcv_result["total_candles"] == 0:
            raise ValueError(f"No hay datos para {request.symbol} en el rango solicitado.")
            
        await notify_ws(job_id, {"event": "progress", "job_id": job_id, "progress": 40, "message": "Datos descargados. Preparando motor..."})
        
        # 2. Convert to DataFrame
        import pandas as pd
        df = pd.DataFrame(ohlcv_result["data"])
        df["timestamp"] = pd.to_datetime(df["t"], unit="s", utc=True)
        df = df.set_index("timestamp")
        df = df.rename(columns={"o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"})
        
        await notify_ws(job_id, {"event": "progress", "job_id": job_id, "progress": 50, "message": "Calculando indicadores y evaluando estrategia..."})
        
        # 3. Run backtest in thread pool to avoid blocking asyncio loop
        result = await asyncio.to_thread(backtest_engine.run_backtest, df, request)
        
        await notify_ws(job_id, {"event": "progress", "job_id": job_id, "progress": 90, "message": "Generando resultados..."})
        
        # 4. Save Results
        completed_time = datetime.now(timezone.utc)
        jobs_db[job_id]["status"] = "completed"
        jobs_db[job_id]["completed_at"] = completed_time.isoformat()
        jobs_db[job_id]["duration_seconds"] = (completed_time - datetime.fromisoformat(jobs_db[job_id]["created_at"])).total_seconds()
        jobs_db[job_id]["result"] = result.model_dump()
        
        await notify_ws(job_id, {
            "event": "completed",
            "job_id": job_id,
            "status": "completed",
            "timestamp": completed_time.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Backtest {job_id} failed: {e}", exc_info=True)
        jobs_db[job_id]["status"] = "failed"
        await notify_ws(job_id, {
            "event": "failed",
            "job_id": job_id,
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })


@router.post("/run", status_code=202)
async def run_backtest(request: BacktestRunRequest, background_tasks: BackgroundTasks):
    """Start a new backtest job."""
    job_id = f"bt_{uuid.uuid4().hex[:8]}"
    
    created_at = datetime.now(timezone.utc).isoformat()
    
    jobs_db[job_id] = {
        "job_id": job_id,
        "name": request.name,
        "status": "queued",
        "created_at": created_at,
        "config": request.model_dump(),
        "result": None
    }
    
    background_tasks.add_task(run_backtest_task, job_id, request)
    
    return {
        "job_id": job_id,
        "status": "queued",
        "websocket_url": f"/ws/backtest/{job_id}",
        "created_at": created_at,
    }


@router.get("/{job_id}")
async def get_backtest(job_id: str):
    """Get backtest job details and results."""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Backtest not found")
        
    return jobs_db[job_id]


@router.delete("/{job_id}")
async def cancel_backtest(job_id: str):
    """Cancel a running backtest."""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Backtest not found")
        
    # Mark as cancelled (the thread might still run until it checks state, but MVP is just setting status)
    jobs_db[job_id]["status"] = "cancelled"
    
    await notify_ws(job_id, {
        "event": "cancelled",
        "job_id": job_id,
        "status": "cancelled",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {"job_id": job_id, "status": "cancelled"}


@router.get("/history/list")
async def get_backtest_history(limit: int = 20, offset: int = 0):
    """Get paginated backtest history."""
    items = []
    # Convert dict values to list and sort by created_at desc
    sorted_jobs = sorted(jobs_db.values(), key=lambda x: x["created_at"], reverse=True)
    
    for job in sorted_jobs[offset:offset+limit]:
        item = {
            "job_id": job["job_id"],
            "name": job["name"],
            "symbol": job["config"]["symbol"],
            "timeframe": job["config"]["timeframe"],
            "status": job["status"],
            "created_at": job["created_at"],
            "net_profit_pct": job["result"]["metrics"]["net_profit_pct"] if job.get("result") else None,
            "win_rate_pct": job["result"]["metrics"]["win_rate_pct"] if job.get("result") else None,
            "total_trades": job["result"]["metrics"]["total_trades"] if job.get("result") else None,
        }
        items.append(item)
        
    return {"items": items, "total": len(jobs_db), "limit": limit, "offset": offset}
