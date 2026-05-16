"""Global state for tracking backtests and websockets."""

from typing import Dict, Any

# WebSocket connections keyed by job_id
active_ws_connections: Dict[str, list] = {}

# In-memory store for active/completed jobs (MVP)
jobs_db: Dict[str, Dict[str, Any]] = {}
