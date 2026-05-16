"""Reports router — endpoints for exporting backtest results as PDF, CSV, JSON."""

import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse

from core.state import jobs_db
from services.report_generator import report_generator

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/{backtest_id}/pdf")
async def export_pdf(backtest_id: str):
    """Export backtest report as PDF."""
    if backtest_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Backtest not found")
        
    job_data = jobs_db[backtest_id]
    if job_data.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Backtest not completed")
        
    pdf_buffer = report_generator.generate_pdf(job_data)
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=backtest_{backtest_id}.pdf"}
    )


@router.get("/{backtest_id}/csv")
async def export_csv(backtest_id: str):
    """Export backtest trades as CSV."""
    if backtest_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Backtest not found")
        
    job_data = jobs_db[backtest_id]
    if job_data.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Backtest not completed")
        
    trades = job_data.get("result", {}).get("trades", [])
    csv_buffer = report_generator.generate_csv(trades)
    
    return StreamingResponse(
        csv_buffer,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=trades_{backtest_id}.csv"}
    )


@router.get("/{backtest_id}/json")
async def export_json(backtest_id: str):
    """Export backtest result as JSON."""
    if backtest_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Backtest not found")
        
    return JSONResponse(
        content=jobs_db[backtest_id],
        headers={"Content-Disposition": f"attachment; filename=backtest_{backtest_id}.json"}
    )
