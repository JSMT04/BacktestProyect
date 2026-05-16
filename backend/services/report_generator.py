"""ReportGenerator — PDF, CSV, and JSON report generation.

Full implementation in FASE 3 (TASK-305 through TASK-308).
"""

import io
import csv
from typing import Dict, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet


class ReportGenerator:
    """Generates backtest reports in PDF, CSV, and JSON formats."""
    
    def generate_pdf(self, job_data: Dict[str, Any]) -> io.BytesIO:
        """Generate a PDF report using reportlab."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        elements.append(Paragraph(f"Backtest Report: {job_data.get('name', 'N/A')}", styles['Title']))
        elements.append(Spacer(1, 12))

        # Config Summary
        config = job_data.get("config", {})
        elements.append(Paragraph(f"<b>Symbol:</b> {config.get('symbol')} | <b>Timeframe:</b> {config.get('timeframe')}", styles['Normal']))
        elements.append(Paragraph(f"<b>Period:</b> {config.get('start')} to {config.get('end')}", styles['Normal']))
        elements.append(Paragraph(f"<b>Initial Capital:</b> ${config.get('initial_capital', 0):.2f}", styles['Normal']))
        elements.append(Spacer(1, 24))

        # Metrics
        result = job_data.get("result", {})
        metrics = result.get("metrics", {})
        
        elements.append(Paragraph("<b>Performance Metrics</b>", styles['Heading2']))
        
        metrics_data = [
            ["Metric", "Value"],
            ["Net Profit ($)", f"${metrics.get('net_profit_usd', 0):.2f}"],
            ["Net Profit (%)", f"{metrics.get('net_profit_pct', 0):.2f}%"],
            ["Win Rate (%)", f"{metrics.get('win_rate_pct', 0):.2f}%"],
            ["Profit Factor", f"{metrics.get('profit_factor', 0):.2f}"],
            ["Max Drawdown (%)", f"{metrics.get('max_drawdown_pct', 0):.2f}%"],
            ["Total Trades", str(metrics.get('total_trades', 0))],
            ["Winning Trades", str(metrics.get('winning_trades', 0))],
            ["Losing Trades", str(metrics.get('losing_trades', 0))],
        ]
        
        t_metrics = Table(metrics_data, colWidths=[200, 150])
        t_metrics.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(t_metrics)
        elements.append(Spacer(1, 24))
        
        # Recent Trades Summary (Top 20)
        trades = result.get("trades", [])
        elements.append(Paragraph(f"<b>Recent Trades (showing up to 20 of {len(trades)})</b>", styles['Heading2']))
        
        trades_data = [["ID", "Dir", "Entry Time", "Entry Price", "Exit Price", "PnL ($)"]]
        for trade in trades[-20:]:
            trades_data.append([
                str(trade.get("trade_id")),
                trade.get("direction"),
                trade.get("entry_time")[:16].replace('T', ' '),
                f"${trade.get('entry_price', 0):.2f}",
                f"${trade.get('exit_price', 0):.2f}",
                f"${trade.get('pnl_usd', 0):.2f}"
            ])
            
        t_trades = Table(trades_data, colWidths=[40, 50, 100, 80, 80, 80])
        t_trades.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(t_trades)

        doc.build(elements)
        buffer.seek(0)
        return buffer

    def generate_csv(self, trades: list) -> io.StringIO:
        """Generate a CSV report of trades."""
        output = io.StringIO()
        if not trades:
            return output
            
        fieldnames = list(trades[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for trade in trades:
            writer.writerow(trade)
            
        output.seek(0)
        return output

report_generator = ReportGenerator()
