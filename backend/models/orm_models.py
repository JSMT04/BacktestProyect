"""SQLAlchemy ORM models matching the DDL contract in STAGE 6.2."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import relationship

from models.database import Base


def _generate_uuid() -> str:
    """Generate a UUID4 string for use as a primary key."""
    return str(uuid.uuid4())


def _utc_now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.utcnow().isoformat()


# =========================================================
# TABLE: users
# =========================================================
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_generate_uuid)
    username = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(String, nullable=False, default=_utc_now_iso)
    updated_at = Column(String, nullable=False, default=_utc_now_iso, onupdate=_utc_now_iso)

    # Relationships
    strategies = relationship("Strategy", back_populates="user", cascade="all, delete-orphan")
    backtest_jobs = relationship("BacktestJob", back_populates="user")


# =========================================================
# TABLE: strategies
# =========================================================
class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(String, primary_key=True, default=_generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    current_version = Column(Integer, nullable=False, default=1)
    created_at = Column(String, nullable=False, default=_utc_now_iso)
    updated_at = Column(String, nullable=False, default=_utc_now_iso, onupdate=_utc_now_iso)

    # Relationships
    user = relationship("User", back_populates="strategies")
    versions = relationship("StrategyVersion", back_populates="strategy", cascade="all, delete-orphan")
    backtest_jobs = relationship("BacktestJob", back_populates="strategy")

    __table_args__ = (
        Index("idx_strategies_user_id", "user_id"),
    )


# =========================================================
# TABLE: strategy_versions
# =========================================================
class StrategyVersion(Base):
    __tablename__ = "strategy_versions"

    id = Column(String, primary_key=True, default=_generate_uuid)
    strategy_id = Column(String, ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    strategy_data = Column(Text, nullable=False)  # JSON serialized
    created_at = Column(String, nullable=False, default=_utc_now_iso)

    # Relationships
    strategy = relationship("Strategy", back_populates="versions")

    __table_args__ = (
        UniqueConstraint("strategy_id", "version", name="uq_strategy_version"),
        Index("idx_sv_strategy_id", "strategy_id"),
    )


# =========================================================
# TABLE: backtest_jobs
# =========================================================
class BacktestJob(Base):
    __tablename__ = "backtest_jobs"

    id = Column(String, primary_key=True, default=_generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    strategy_id = Column(String, ForeignKey("strategies.id", ondelete="SET NULL"), nullable=True)
    name = Column(String, nullable=False)
    status = Column(
        String,
        nullable=False,
        default="queued",
    )
    symbol = Column(String, nullable=False)
    timeframe = Column(String, nullable=False)
    start_date = Column(String, nullable=False)
    end_date = Column(String, nullable=False)
    config_json = Column(Text, nullable=False)  # BacktestConfig serialized
    error_message = Column(Text, nullable=True)
    progress_pct = Column(Float, default=0.0)
    created_at = Column(String, nullable=False, default=_utc_now_iso)
    started_at = Column(String, nullable=True)
    completed_at = Column(String, nullable=True)

    # Relationships
    user = relationship("User", back_populates="backtest_jobs")
    strategy = relationship("Strategy", back_populates="backtest_jobs")
    result = relationship("BacktestResult", back_populates="job", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "status IN ('queued','running','completed','failed','cancelled')",
            name="ck_jobs_status",
        ),
        Index("idx_jobs_user_id", "user_id"),
        Index("idx_jobs_status", "status"),
        Index("idx_jobs_created_at", "created_at"),
    )


# =========================================================
# TABLE: backtest_results
# =========================================================
class BacktestResult(Base):
    __tablename__ = "backtest_results"

    id = Column(String, primary_key=True, default=_generate_uuid)
    job_id = Column(String, ForeignKey("backtest_jobs.id", ondelete="CASCADE"), nullable=False, unique=True)
    metrics_json = Column(Text, nullable=False)      # BacktestMetrics serialized
    trades_json = Column(Text, nullable=False)        # Array of Trade serialized
    equity_curve_json = Column(Text, nullable=False)  # Array [{t, equity, drawdown_pct}]
    created_at = Column(String, nullable=False, default=_utc_now_iso)

    # Relationships
    job = relationship("BacktestJob", back_populates="result")


# =========================================================
# TABLE: data_cache_metadata
# =========================================================
class DataCacheMetadata(Base):
    __tablename__ = "data_cache_metadata"

    id = Column(String, primary_key=True, default=_generate_uuid)
    symbol = Column(String, nullable=False)
    timeframe = Column(String, nullable=False)
    start_date = Column(String, nullable=False)
    end_date = Column(String, nullable=False)
    source = Column(String, nullable=False)  # 'yfinance', 'binance', 'alpha_vantage'
    parquet_path = Column(String, nullable=False)
    total_candles = Column(Integer, nullable=False)
    downloaded_at = Column(String, nullable=False, default=_utc_now_iso)

    __table_args__ = (
        UniqueConstraint("symbol", "timeframe", "start_date", "end_date", name="uq_cache_entry"),
        Index("idx_cache_symbol_tf", "symbol", "timeframe"),
    )
