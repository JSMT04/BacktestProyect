"""Application configuration loaded from environment variables via pydantic-settings."""

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """BacktestPro configuration — all values come from .env or environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Data Sources ---
    alpha_vantage_key: str = "your_key_here"
    binance_api_key: str = "your_key_here"
    binance_api_secret: str = "your_secret_here"

    # --- Database ---
    database_url: str = "sqlite+aiosqlite:///./data/backtestpro.db"

    # --- Server ---
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_port: int = 3000
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # --- Security ---
    secret_key: str = "CHANGE_THIS_TO_A_RANDOM_64_CHAR_STRING"
    auth_enabled: bool = False
    access_token_expire_minutes: int = 10080  # 7 days

    # --- Cache ---
    cache_dir: str = "./data/cache"
    cache_max_age_hours: int = 24
    max_cache_size_gb: int = 10

    # --- Backtesting ---
    max_backtest_workers: int = 4
    max_candles_limit: int = 500000

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse comma-separated CORS_ORIGINS into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Singleton instance — import this throughout the application
settings = Settings()
