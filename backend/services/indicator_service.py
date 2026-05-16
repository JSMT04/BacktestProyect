"""IndicatorService — pandas-ta wrapper for technical indicator calculation.

TASK-112: Calculates EMA, SMA, RSI, MACD, Bollinger Bands, and more
using pandas-ta-classic. No lookahead bias: indicators are calculated
on the full historical data and null values at the start are preserved.
"""

import logging
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger("backtestpro.indicator_service")


class IndicatorService:
    """Calculates technical indicators using pandas-ta-classic."""

    # Supported indicator types and their pandas-ta functions
    SUPPORTED_INDICATORS = {
        "SMA", "EMA", "WMA", "DEMA", "TEMA",
        "RSI", "MACD", "BBANDS",
        "ATR", "ADX", "CCI", "STOCH",
        "VWAP", "OBV", "MFI",
    }

    def calculate(
        self,
        df: pd.DataFrame,
        indicators: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculate multiple indicators on OHLCV data.

        Args:
            df: DataFrame with columns [open, high, low, close, volume] and DatetimeIndex
            indicators: List of indicator configs from the API request

        Returns:
            Dict of indicator results keyed by indicator id
        """
        results = {}

        for config in indicators:
            ind_id = config["id"]
            ind_type = config["type"].upper()
            params = config.get("params", {})
            panel = config.get("panel", "main")

            try:
                if ind_type in ("SMA", "EMA", "WMA", "DEMA", "TEMA"):
                    results[ind_id] = self._calc_moving_average(df, ind_type, params, panel)
                elif ind_type == "RSI":
                    results[ind_id] = self._calc_rsi(df, params, panel)
                elif ind_type == "MACD":
                    results[ind_id] = self._calc_macd(df, params, panel)
                elif ind_type == "BBANDS":
                    results[ind_id] = self._calc_bbands(df, params, panel)
                elif ind_type == "ATR":
                    results[ind_id] = self._calc_atr(df, params, panel)
                elif ind_type == "ADX":
                    results[ind_id] = self._calc_adx(df, params, panel)
                elif ind_type == "STOCH":
                    results[ind_id] = self._calc_stoch(df, params, panel)
                elif ind_type == "CCI":
                    results[ind_id] = self._calc_cci(df, params, panel)
                elif ind_type == "OBV":
                    results[ind_id] = self._calc_obv(df, panel)
                elif ind_type == "MFI":
                    results[ind_id] = self._calc_mfi(df, params, panel)
                elif ind_type == "VWAP":
                    results[ind_id] = self._calc_vwap(df, panel)
                else:
                    logger.warning(f"Unsupported indicator type: {ind_type}")
                    continue

            except Exception as e:
                logger.error(f"Error calculating {ind_type} ({ind_id}): {e}")
                continue

        return results

    # =========================================================
    # INDIVIDUAL INDICATOR CALCULATIONS
    # =========================================================

    def _calc_moving_average(
        self, df: pd.DataFrame, ma_type: str, params: Dict, panel: str
    ) -> Dict:
        """Calculate moving average (SMA, EMA, WMA, DEMA, TEMA)."""
        import pandas_ta as ta

        length = int(params.get("length", 20))
        source = params.get("source", "close")
        series = df[source]

        ma_funcs = {
            "SMA": ta.sma,
            "EMA": ta.ema,
            "WMA": ta.wma,
            "DEMA": ta.dema,
            "TEMA": ta.tema,
        }

        result = ma_funcs[ma_type](series, length=length)
        return {
            "panel": panel,
            "type": "line",
            "data": self._series_to_points(df, result),
        }

    def _calc_rsi(self, df: pd.DataFrame, params: Dict, panel: str) -> Dict:
        """Calculate RSI (Relative Strength Index)."""
        import pandas_ta as ta

        length = int(params.get("length", 14))
        result = ta.rsi(df["close"], length=length)
        return {
            "panel": panel,
            "type": "line",
            "overbought": 70,
            "oversold": 30,
            "data": self._series_to_points(df, result),
        }

    def _calc_macd(self, df: pd.DataFrame, params: Dict, panel: str) -> Dict:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        import pandas_ta as ta

        fast = int(params.get("fast", 12))
        slow = int(params.get("slow", 26))
        signal = int(params.get("signal", 9))

        macd_df = ta.macd(df["close"], fast=fast, slow=slow, signal=signal)

        if macd_df is None or macd_df.empty:
            return {"panel": panel, "type": "macd", "macd": [], "signal": [], "histogram": []}

        # pandas-ta MACD columns: MACD_{fast}_{slow}_{signal}, MACDh_{...}, MACDs_{...}
        cols = macd_df.columns.tolist()
        macd_col = [c for c in cols if c.startswith("MACD_")][0] if any(c.startswith("MACD_") for c in cols) else cols[0]
        hist_col = [c for c in cols if c.startswith("MACDh_")][0] if any(c.startswith("MACDh_") for c in cols) else cols[1]
        signal_col = [c for c in cols if c.startswith("MACDs_")][0] if any(c.startswith("MACDs_") for c in cols) else cols[2]

        return {
            "panel": panel,
            "type": "macd",
            "macd": self._series_to_points(df, macd_df[macd_col]),
            "signal": self._series_to_points(df, macd_df[signal_col]),
            "histogram": self._series_to_points(df, macd_df[hist_col]),
        }

    def _calc_bbands(self, df: pd.DataFrame, params: Dict, panel: str) -> Dict:
        """Calculate Bollinger Bands."""
        import pandas_ta as ta

        length = int(params.get("length", 20))
        std = float(params.get("std", 2.0))

        bb_df = ta.bbands(df["close"], length=length, std=std)

        if bb_df is None or bb_df.empty:
            return {"panel": panel, "type": "bands", "upper": [], "middle": [], "lower": []}

        cols = bb_df.columns.tolist()
        lower_col = [c for c in cols if "BBL" in c][0] if any("BBL" in c for c in cols) else cols[0]
        mid_col = [c for c in cols if "BBM" in c][0] if any("BBM" in c for c in cols) else cols[1]
        upper_col = [c for c in cols if "BBU" in c][0] if any("BBU" in c for c in cols) else cols[2]

        return {
            "panel": panel,
            "type": "bands",
            "upper": self._series_to_points(df, bb_df[upper_col]),
            "middle": self._series_to_points(df, bb_df[mid_col]),
            "lower": self._series_to_points(df, bb_df[lower_col]),
        }

    def _calc_atr(self, df: pd.DataFrame, params: Dict, panel: str) -> Dict:
        """Calculate ATR (Average True Range)."""
        import pandas_ta as ta

        length = int(params.get("length", 14))
        result = ta.atr(df["high"], df["low"], df["close"], length=length)
        return {
            "panel": panel,
            "type": "line",
            "data": self._series_to_points(df, result),
        }

    def _calc_adx(self, df: pd.DataFrame, params: Dict, panel: str) -> Dict:
        """Calculate ADX (Average Directional Index)."""
        import pandas_ta as ta

        length = int(params.get("length", 14))
        result = ta.adx(df["high"], df["low"], df["close"], length=length)

        if result is None or result.empty:
            return {"panel": panel, "type": "line", "data": []}

        adx_col = [c for c in result.columns if "ADX" in c and "DM" not in c][0]
        return {
            "panel": panel,
            "type": "line",
            "data": self._series_to_points(df, result[adx_col]),
        }

    def _calc_stoch(self, df: pd.DataFrame, params: Dict, panel: str) -> Dict:
        """Calculate Stochastic Oscillator."""
        import pandas_ta as ta

        k = int(params.get("k", 14))
        d = int(params.get("d", 3))
        result = ta.stoch(df["high"], df["low"], df["close"], k=k, d=d)

        if result is None or result.empty:
            return {"panel": panel, "type": "line", "data": []}

        k_col = result.columns[0]
        return {
            "panel": panel,
            "type": "line",
            "overbought": 80,
            "oversold": 20,
            "data": self._series_to_points(df, result[k_col]),
        }

    def _calc_cci(self, df: pd.DataFrame, params: Dict, panel: str) -> Dict:
        """Calculate CCI (Commodity Channel Index)."""
        import pandas_ta as ta

        length = int(params.get("length", 20))
        result = ta.cci(df["high"], df["low"], df["close"], length=length)
        return {
            "panel": panel,
            "type": "line",
            "data": self._series_to_points(df, result),
        }

    def _calc_obv(self, df: pd.DataFrame, panel: str) -> Dict:
        """Calculate OBV (On-Balance Volume)."""
        import pandas_ta as ta

        result = ta.obv(df["close"], df["volume"])
        return {
            "panel": panel,
            "type": "line",
            "data": self._series_to_points(df, result),
        }

    def _calc_mfi(self, df: pd.DataFrame, params: Dict, panel: str) -> Dict:
        """Calculate MFI (Money Flow Index)."""
        import pandas_ta as ta

        length = int(params.get("length", 14))
        result = ta.mfi(df["high"], df["low"], df["close"], df["volume"], length=length)
        return {
            "panel": panel,
            "type": "line",
            "overbought": 80,
            "oversold": 20,
            "data": self._series_to_points(df, result),
        }

    def _calc_vwap(self, df: pd.DataFrame, panel: str) -> Dict:
        """Calculate VWAP (Volume Weighted Average Price)."""
        import pandas_ta as ta

        result = ta.vwap(df["high"], df["low"], df["close"], df["volume"])
        return {
            "panel": panel,
            "type": "line",
            "data": self._series_to_points(df, result),
        }

    # =========================================================
    # HELPERS
    # =========================================================

    def _series_to_points(
        self, df: pd.DataFrame, series: Optional[pd.Series]
    ) -> List[Dict]:
        """Convert a pandas Series to [{t, v}] format, skipping NaN values."""
        if series is None:
            return []

        points = []
        for idx, val in series.items():
            if pd.isna(val):
                continue
            ts = int(idx.timestamp()) if hasattr(idx, "timestamp") else int(idx)
            points.append({"t": ts, "v": round(float(val), 8)})
        return points


# Singleton instance
indicator_service = IndicatorService()
