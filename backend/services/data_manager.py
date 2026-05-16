"""DataManager — Cache management and data download orchestrator.

Handles:
- Automatic source detection by symbol pattern
- Parquet cache read/write with freshness validation
- Downloads from yfinance, CCXT/Binance, Alpha Vantage
"""

import hashlib
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from core.config import settings

logger = logging.getLogger("backtestpro.data_manager")


# =========================================================
# TIMEFRAME MAPPING
# =========================================================
TIMEFRAME_MAP_YFINANCE = {
    "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "1h", "4h": "4h",  # yfinance doesn't have 4h, we'll resample
    "1d": "1d", "1w": "1wk", "1M": "1mo",
}

TIMEFRAME_MAP_CCXT = {
    "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "1h", "4h": "4h", "1d": "1d", "1w": "1w", "1M": "1M",
}

TIMEFRAME_SECONDS = {
    "1m": 60, "5m": 300, "15m": 900, "30m": 1800,
    "1h": 3600, "4h": 14400, "1d": 86400, "1w": 604800, "1M": 2592000,
}


class DataManager:
    """Manages OHLCV data retrieval with caching and source detection."""

    def __init__(self) -> None:
        self.cache_dir = settings.cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    # =========================================================
    # PUBLIC API
    # =========================================================

    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start: str,
        end: str,
        force_refresh: bool = False,
    ) -> Dict:
        """Get OHLCV data for a symbol, using cache when possible.

        Args:
            symbol: Trading pair or ticker (e.g., "BTC/USDT", "AAPL", "EURUSD=X")
            timeframe: Candle timeframe (e.g., "1h", "1d")
            start: ISO 8601 start date
            end: ISO 8601 end date
            force_refresh: If True, bypass cache and download fresh data

        Returns:
            Dict with symbol, timeframe, source, from_cache, data array, etc.
        """
        source = self._detect_source(symbol)
        cache_key = self._cache_key(symbol, timeframe, start, end)
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.parquet")

        # Try cache first
        if not force_refresh and os.path.exists(cache_path):
            cache_age_hours = self._cache_age_hours(cache_path)
            if cache_age_hours < settings.cache_max_age_hours:
                logger.info(f"Cache hit for {symbol} {timeframe} (age: {cache_age_hours:.1f}h)")
                df = self._read_cache(cache_path)
                data = self._df_to_ohlcv_list(df)
                return {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "start": start,
                    "end": end,
                    "source": source,
                    "from_cache": True,
                    "cache_age_hours": round(cache_age_hours, 1),
                    "total_candles": len(data),
                    "data": data,
                }

        # Download fresh data
        logger.info(f"Downloading {symbol} {timeframe} from {source}")
        df = await self._download(symbol, timeframe, start, end, source)

        if df is None or df.empty:
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "start": start,
                "end": end,
                "source": source,
                "from_cache": False,
                "cache_age_hours": None,
                "total_candles": 0,
                "data": [],
            }

        # Save to cache
        self._write_cache(cache_path, df)

        data = self._df_to_ohlcv_list(df)
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "start": start,
            "end": end,
            "source": source,
            "from_cache": False,
            "cache_age_hours": 0.0,
            "total_candles": len(data),
            "data": data,
        }

    def search_symbols(self, query: str, limit: int = 10) -> Dict:
        """Search for symbols across known lists.

        Returns matching symbols from crypto, forex, and stock catalogs.
        """
        query_upper = query.upper().strip()
        results = []

        # Crypto pairs (Binance-style)
        crypto_pairs = [
            ("BTC/USDT", "Bitcoin / Tether USD", "Binance", "BTC", "USDT"),
            ("ETH/USDT", "Ethereum / Tether USD", "Binance", "ETH", "USDT"),
            ("BNB/USDT", "BNB / Tether USD", "Binance", "BNB", "USDT"),
            ("SOL/USDT", "Solana / Tether USD", "Binance", "SOL", "USDT"),
            ("XRP/USDT", "Ripple / Tether USD", "Binance", "XRP", "USDT"),
            ("ADA/USDT", "Cardano / Tether USD", "Binance", "ADA", "USDT"),
            ("DOGE/USDT", "Dogecoin / Tether USD", "Binance", "DOGE", "USDT"),
            ("DOT/USDT", "Polkadot / Tether USD", "Binance", "DOT", "USDT"),
            ("AVAX/USDT", "Avalanche / Tether USD", "Binance", "AVAX", "USDT"),
            ("LINK/USDT", "Chainlink / Tether USD", "Binance", "LINK", "USDT"),
            ("MATIC/USDT", "Polygon / Tether USD", "Binance", "MATIC", "USDT"),
            ("UNI/USDT", "Uniswap / Tether USD", "Binance", "UNI", "USDT"),
            ("ATOM/USDT", "Cosmos / Tether USD", "Binance", "ATOM", "USDT"),
            ("LTC/USDT", "Litecoin / Tether USD", "Binance", "LTC", "USDT"),
            ("ETH/BTC", "Ethereum / Bitcoin", "Binance", "ETH", "BTC"),
            ("BTC/BUSD", "Bitcoin / Binance USD", "Binance", "BTC", "BUSD"),
        ]

        for sym, name, exch, base, quote in crypto_pairs:
            if query_upper in sym.upper() or query_upper in name.upper() or query_upper in base:
                results.append({
                    "symbol": sym,
                    "name": name,
                    "type": "crypto",
                    "exchange": exch,
                    "base_currency": base,
                    "quote_currency": quote,
                })

        # Forex pairs
        forex_pairs = [
            ("EURUSD=X", "Euro / US Dollar", "FX", "EUR", "USD"),
            ("GBPUSD=X", "British Pound / US Dollar", "FX", "GBP", "USD"),
            ("USDJPY=X", "US Dollar / Japanese Yen", "FX", "USD", "JPY"),
            ("USDCHF=X", "US Dollar / Swiss Franc", "FX", "USD", "CHF"),
            ("AUDUSD=X", "Australian Dollar / US Dollar", "FX", "AUD", "USD"),
            ("USDCAD=X", "US Dollar / Canadian Dollar", "FX", "USD", "CAD"),
            ("NZDUSD=X", "New Zealand Dollar / US Dollar", "FX", "NZD", "USD"),
            ("EURGBP=X", "Euro / British Pound", "FX", "EUR", "GBP"),
            ("EURJPY=X", "Euro / Japanese Yen", "FX", "EUR", "JPY"),
            ("GBPJPY=X", "British Pound / Japanese Yen", "FX", "GBP", "JPY"),
        ]

        for sym, name, exch, base, quote in forex_pairs:
            if query_upper in sym.upper() or query_upper in name.upper() or query_upper in base or query_upper in quote:
                results.append({
                    "symbol": sym,
                    "name": name,
                    "type": "forex",
                    "exchange": exch,
                    "base_currency": base,
                    "quote_currency": quote,
                })

        # Stocks (popular US stocks)
        stocks = [
            ("AAPL", "Apple Inc.", "NASDAQ", "USD"),
            ("MSFT", "Microsoft Corporation", "NASDAQ", "USD"),
            ("GOOGL", "Alphabet Inc.", "NASDAQ", "USD"),
            ("AMZN", "Amazon.com Inc.", "NASDAQ", "USD"),
            ("TSLA", "Tesla Inc.", "NASDAQ", "USD"),
            ("META", "Meta Platforms Inc.", "NASDAQ", "USD"),
            ("NVDA", "NVIDIA Corporation", "NASDAQ", "USD"),
            ("JPM", "JPMorgan Chase & Co.", "NYSE", "USD"),
            ("V", "Visa Inc.", "NYSE", "USD"),
            ("MA", "Mastercard Inc.", "NYSE", "USD"),
            ("DIS", "The Walt Disney Company", "NYSE", "USD"),
            ("NFLX", "Netflix Inc.", "NASDAQ", "USD"),
            ("AMD", "Advanced Micro Devices", "NASDAQ", "USD"),
            ("PYPL", "PayPal Holdings Inc.", "NASDAQ", "USD"),
            ("BA", "Boeing Company", "NYSE", "USD"),
            ("SPY", "SPDR S&P 500 ETF", "NYSE", "USD"),
            ("QQQ", "Invesco QQQ Trust", "NASDAQ", "USD"),
        ]

        for sym, name, exch, currency in stocks:
            if query_upper in sym.upper() or query_upper in name.upper():
                results.append({
                    "symbol": sym,
                    "name": name,
                    "type": "stock",
                    "exchange": exch,
                    "base_currency": currency,
                    "quote_currency": None,
                })

        # Commodities
        commodities = [
            ("GC=F", "Gold Futures", "COMEX", "USD"),
            ("SI=F", "Silver Futures", "COMEX", "USD"),
            ("CL=F", "Crude Oil WTI Futures", "NYMEX", "USD"),
            ("NG=F", "Natural Gas Futures", "NYMEX", "USD"),
        ]

        for sym, name, exch, currency in commodities:
            if query_upper in sym.upper() or query_upper in name.upper():
                results.append({
                    "symbol": sym,
                    "name": name,
                    "type": "commodity",
                    "exchange": exch,
                    "base_currency": currency,
                    "quote_currency": None,
                })

        return {
            "results": results[:limit],
            "total": len(results),
        }

    # =========================================================
    # SOURCE DETECTION
    # =========================================================

    def _detect_source(self, symbol: str) -> str:
        """Detect the data source based on symbol pattern.

        Rules:
        - Contains "/" → crypto (Binance via CCXT)
        - Ends with "=X" → forex (yfinance, Alpha Vantage for intraday)
        - Ends with "=F" → commodity (yfinance)
        - Everything else → stock (yfinance)
        """
        if "/" in symbol:
            return "binance"
        elif symbol.endswith("=X"):
            return "yfinance"  # Alpha Vantage for intraday < 1d
        elif symbol.endswith("=F"):
            return "yfinance"
        else:
            return "yfinance"

    # =========================================================
    # DOWNLOAD METHODS
    # =========================================================

    async def _download(
        self,
        symbol: str,
        timeframe: str,
        start: str,
        end: str,
        source: str,
    ) -> Optional[pd.DataFrame]:
        """Route download to the appropriate source."""
        try:
            if source == "binance":
                return await self._download_binance(symbol, timeframe, start, end)
            elif source == "alpha_vantage":
                return await self._download_alpha_vantage(symbol, timeframe, start, end)
            else:
                return await self._download_yfinance(symbol, timeframe, start, end)
        except Exception as e:
            logger.error(f"Download failed for {symbol} from {source}: {e}")
            return None

    async def _download_yfinance(
        self, symbol: str, timeframe: str, start: str, end: str
    ) -> Optional[pd.DataFrame]:
        """Download data from yfinance (stocks, forex daily, indices, commodities).

        TASK-103: Implements yfinance download.
        """
        import yfinance as yf

        yf_interval = TIMEFRAME_MAP_YFINANCE.get(timeframe, "1d")

        # yfinance has limitations on intraday data range
        # For intervals < 1d, max period depends on interval
        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))

        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(
                start=start_dt.strftime("%Y-%m-%d"),
                end=end_dt.strftime("%Y-%m-%d"),
                interval=yf_interval,
                auto_adjust=True,
            )

            if df is None or df.empty:
                logger.warning(f"yfinance returned no data for {symbol}")
                return None

            # Standardize columns
            df = df.rename(columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            })

            # Keep only OHLCV columns
            df = df[["open", "high", "low", "close", "volume"]].copy()
            df.index = pd.to_datetime(df.index, utc=True)
            df = df.dropna()

            # Handle 4h resampling if yfinance doesn't support it natively
            if timeframe == "4h" and yf_interval == "1h":
                df = self._resample(df, "4h")

            logger.info(f"yfinance: Downloaded {len(df)} candles for {symbol}")
            return df

        except Exception as e:
            logger.error(f"yfinance download error for {symbol}: {e}")
            return None

    async def _download_binance(
        self, symbol: str, timeframe: str, start: str, end: str
    ) -> Optional[pd.DataFrame]:
        """Download data from Binance via CCXT.

        TASK-104: Implements crypto data download.
        """
        import ccxt

        ccxt_timeframe = TIMEFRAME_MAP_CCXT.get(timeframe, "1h")

        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
        since_ms = int(start_dt.timestamp() * 1000)
        end_ms = int(end_dt.timestamp() * 1000)

        try:
            exchange = ccxt.binance({
                "apiKey": settings.binance_api_key if settings.binance_api_key != "your_key_here" else None,
                "secret": settings.binance_api_secret if settings.binance_api_secret != "your_secret_here" else None,
                "enableRateLimit": True,
            })

            all_ohlcv = []
            current_since = since_ms
            batch_limit = 1000  # Binance max per request

            while current_since < end_ms:
                ohlcv = exchange.fetch_ohlcv(
                    symbol,
                    timeframe=ccxt_timeframe,
                    since=current_since,
                    limit=batch_limit,
                )

                if not ohlcv:
                    break

                all_ohlcv.extend(ohlcv)

                # Move to next batch
                last_ts = ohlcv[-1][0]
                if last_ts <= current_since:
                    break
                current_since = last_ts + 1

                # Safety check
                if len(all_ohlcv) >= settings.max_candles_limit:
                    logger.warning(f"Hit candle limit ({settings.max_candles_limit}) for {symbol}")
                    break

            if not all_ohlcv:
                logger.warning(f"CCXT returned no data for {symbol}")
                return None

            # Convert to DataFrame
            df = pd.DataFrame(
                all_ohlcv,
                columns=["timestamp", "open", "high", "low", "close", "volume"],
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
            df = df.set_index("timestamp")

            # Filter to requested range
            df = df[df.index <= pd.Timestamp(end_dt)]
            df = df.dropna()

            logger.info(f"Binance: Downloaded {len(df)} candles for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Binance download error for {symbol}: {e}")
            return None

    async def _download_alpha_vantage(
        self, symbol: str, timeframe: str, start: str, end: str
    ) -> Optional[pd.DataFrame]:
        """Download forex intraday data from Alpha Vantage.

        TASK-105: Implements Alpha Vantage download.
        Note: Alpha Vantage has strict rate limits on the free tier.
        """
        if settings.alpha_vantage_key == "your_key_here":
            logger.warning("Alpha Vantage API key not configured, falling back to yfinance")
            return await self._download_yfinance(symbol, timeframe, start, end)

        try:
            from alpha_vantage.foreignexchange import ForeignExchange

            # Extract currency pair from symbol (e.g., "EURUSD=X" -> "EUR", "USD")
            clean_symbol = symbol.replace("=X", "")
            from_currency = clean_symbol[:3]
            to_currency = clean_symbol[3:]

            fx = ForeignExchange(key=settings.alpha_vantage_key, output_format="pandas")

            # Map timeframe to Alpha Vantage interval
            av_interval_map = {
                "1m": "1min", "5m": "5min", "15m": "15min", "30m": "30min", "1h": "60min",
            }

            if timeframe in av_interval_map:
                df, _ = fx.get_currency_exchange_intraday(
                    from_symbol=from_currency,
                    to_symbol=to_currency,
                    interval=av_interval_map[timeframe],
                    outputsize="full",
                )
            else:
                df, _ = fx.get_currency_exchange_daily(
                    from_symbol=from_currency,
                    to_symbol=to_currency,
                    outputsize="full",
                )

            if df is None or df.empty:
                return None

            # Standardize columns
            df.columns = [c.split(". ")[1] if ". " in c else c for c in df.columns]
            df = df.rename(columns={"open": "open", "high": "high", "low": "low", "close": "close"})

            # Alpha Vantage doesn't provide volume for forex, fill with 0
            if "volume" not in df.columns:
                df["volume"] = 0.0

            df = df[["open", "high", "low", "close", "volume"]].copy()
            df.index = pd.to_datetime(df.index, utc=True)
            df = df.sort_index()

            # Filter to requested date range
            start_dt = pd.Timestamp(datetime.fromisoformat(start.replace("Z", "+00:00")))
            end_dt = pd.Timestamp(datetime.fromisoformat(end.replace("Z", "+00:00")))
            df = df[(df.index >= start_dt) & (df.index <= end_dt)]

            logger.info(f"Alpha Vantage: Downloaded {len(df)} candles for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Alpha Vantage download error for {symbol}: {e}")
            return await self._download_yfinance(symbol, timeframe, start, end)

    # =========================================================
    # CACHE OPERATIONS
    # =========================================================

    def _cache_key(self, symbol: str, timeframe: str, start: str, end: str) -> str:
        """Generate a deterministic cache key from parameters."""
        raw = f"{symbol}_{timeframe}_{start}_{end}"
        return hashlib.md5(raw.encode()).hexdigest()

    def _cache_age_hours(self, cache_path: str) -> float:
        """Calculate age of a cache file in hours."""
        if not os.path.exists(cache_path):
            return float("inf")
        mtime = os.path.getmtime(cache_path)
        age_seconds = time.time() - mtime
        return age_seconds / 3600.0

    def _read_cache(self, cache_path: str) -> pd.DataFrame:
        """Read cached OHLCV data from Parquet file."""
        df = pd.read_parquet(cache_path)
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index, utc=True)
        return df

    def _write_cache(self, cache_path: str, df: pd.DataFrame) -> None:
        """Write OHLCV DataFrame to Parquet cache."""
        try:
            df.to_parquet(cache_path, engine="pyarrow", compression="snappy")
            logger.info(f"Cache written: {cache_path} ({len(df)} rows)")
        except Exception as e:
            logger.error(f"Failed to write cache: {e}")

    # =========================================================
    # DATA TRANSFORMATION
    # =========================================================

    def _df_to_ohlcv_list(self, df: pd.DataFrame) -> List[Dict]:
        """Convert a DataFrame to the API response format.

        Each row becomes {t: unix_timestamp, o, h, l, c, v}.
        """
        records = []
        for idx, row in df.iterrows():
            ts = int(idx.timestamp()) if hasattr(idx, "timestamp") else int(idx)
            records.append({
                "t": ts,
                "o": round(float(row["open"]), 8),
                "h": round(float(row["high"]), 8),
                "l": round(float(row["low"]), 8),
                "c": round(float(row["close"]), 8),
                "v": round(float(row["volume"]), 8),
            })
        return records

    def _resample(self, df: pd.DataFrame, target_tf: str) -> pd.DataFrame:
        """Resample OHLCV data to a larger timeframe."""
        rule_map = {"4h": "4h", "1d": "1D", "1w": "1W", "1M": "1ME"}
        rule = rule_map.get(target_tf, target_tf)

        resampled = df.resample(rule).agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }).dropna()

        return resampled


# Singleton instance
data_manager = DataManager()
