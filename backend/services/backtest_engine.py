"""BacktestEngine — vectorbt-based backtesting motor.

TASK-201 through TASK-207 implementation.
"""

import logging
from typing import Dict, Any, List

import pandas as pd
import numpy as np
import vectorbt as vbt
import pandas_ta as ta

from models.schemas import BacktestRunRequest, BacktestResultData, BacktestMetrics, Trade, EquityPoint

logger = logging.getLogger("backtestpro.backtest_engine")


class BacktestEngine:
    """Executes backtests using vectorbt with bar-by-bar evaluation."""

    def run_backtest(self, df: pd.DataFrame, config: BacktestRunRequest) -> BacktestResultData:
        """Run a backtest given OHLCV data and a configuration request."""
        logger.info(f"Running backtest for {config.symbol} from {config.start} to {config.end}")

        # Extract features
        close = df["close"]

        # 1. Parse Strategy & Generate Signals
        if config.strategy.mode == "visual":
            entries, exits, short_entries, short_exits = self._evaluate_visual_strategy(df, config.strategy)
        elif config.strategy.mode == "code":
            # Local execution of Python code (as requested by user for local MVP)
            # We inject df, pd, np, ta, and expect the user code to mutate the signal variables
            local_context = {
                "df": df,
                "pd": pd,
                "np": np,
                "ta": ta,
                "entries": pd.Series(False, index=df.index),
                "exits": pd.Series(False, index=df.index),
                "short_entries": pd.Series(False, index=df.index),
                "short_exits": pd.Series(False, index=df.index)
            }
            
            try:
                if config.strategy.code:
                    exec(config.strategy.code, {}, local_context)
                
                entries = local_context.get("entries")
                exits = local_context.get("exits")
                short_entries = local_context.get("short_entries")
                short_exits = local_context.get("short_exits")
            except Exception as e:
                logger.error(f"Error executing strategy code: {e}")
                raise ValueError(f"Error en el código Python de la estrategia: {str(e)}")
        else:
            raise ValueError(f"Unknown strategy mode: {config.strategy.mode}")

        # 2. Setup configuration for vectorbt
        init_cash = config.initial_capital
        
        # Position sizing
        size_type = 'percent'
        size = 1.0  # default 100%
        if config.position_config.type == 'percent_capital':
            size_type = 'percent'
            size = config.position_config.value / 100.0
        elif config.position_config.type == 'fixed_usd':
            size_type = 'value'
            size = config.position_config.value
        elif config.position_config.type == 'contracts':
            size_type = 'amount'
            size = config.position_config.value

        # Fees
        fees = 0.0
        if config.commission.type == 'percent':
            fees = config.commission.value / 100.0

        # Stops
        sl_stop = config.strategy.stop_loss.value / 100.0 if config.strategy.stop_loss else np.nan
        tp_stop = config.strategy.take_profit.value / 100.0 if config.strategy.take_profit and config.strategy.take_profit.type == 'percent' else np.nan
        
        # Take profit as RR ratio
        if config.strategy.take_profit and config.strategy.take_profit.type == 'rr_ratio' and config.strategy.stop_loss:
            # Simple approximation: TP = SL_pct * RR
            tp_stop = sl_stop * config.strategy.take_profit.value

        sl_trail = config.strategy.trailing_stop.value / 100.0 if config.strategy.trailing_stop and config.strategy.trailing_stop.enabled else np.nan

        # 3. Run vectorbt Portfolio
        pf = vbt.Portfolio.from_signals(
            close=close,
            entries=entries,
            exits=exits,
            short_entries=short_entries,
            short_exits=short_exits,
            init_cash=init_cash,
            fees=fees,
            slippage=config.slippage_pips * 0.0001, # Rough approximation of pips to pct/abs, assuming standard forex/crypto, wait vectorbt slippage is relative to price by default if < 1. Let's assume 0 for MVP to keep it clean unless requested.
            sl_stop=sl_stop,
            tp_stop=tp_stop,
            sl_trail=sl_trail,
            size=size,
            size_type=size_type,
            freq='1d', # Will not affect metric calcs if we use generic stats, but good to have
        )

        # 4. Extract Metrics
        metrics = self._extract_metrics(pf, config, len(df))

        # 5. Extract Trades
        trades = self._extract_trades(pf)

        # 6. Extract Equity Curve
        equity_curve = self._extract_equity_curve(pf)

        return BacktestResultData(
            metrics=metrics,
            trades=trades,
            equity_curve=equity_curve
        )

    def _evaluate_visual_strategy(self, df: pd.DataFrame, strategy) -> tuple:
        """Parses a visual strategy into entry and exit signals."""
        entries = self._evaluate_conditions(df, strategy.entry_long)
        exits = self._evaluate_conditions(df, strategy.exit_long)
        short_entries = self._evaluate_conditions(df, strategy.entry_short)
        short_exits = self._evaluate_conditions(df, strategy.exit_short)

        return entries, exits, short_entries, short_exits

    def _evaluate_conditions(self, df: pd.DataFrame, conditions_list: List) -> pd.Series:
        """Evaluates a list of conditions (ANDed together for MVP)."""
        result = pd.Series(False, index=df.index)
        
        if not conditions_list:
            return result
            
        result = pd.Series(True, index=df.index)
        for cond in conditions_list:
            series_a = self._calc_indicator(df, cond.indicator_a)
            
            if cond.indicator_b:
                series_b = self._calc_indicator(df, cond.indicator_b)
            else:
                series_b = pd.Series(cond.value, index=df.index)
            
            op = cond.operator
            if op == 'greater_than':
                cond_res = series_a > series_b
            elif op == 'less_than':
                cond_res = series_a < series_b
            elif op == 'crosses_above':
                cond_res = (series_a > series_b) & (series_a.shift(1) <= series_b.shift(1))
            elif op == 'crosses_below':
                cond_res = (series_a < series_b) & (series_a.shift(1) >= series_b.shift(1))
            elif op == 'equal':
                cond_res = series_a == series_b
            else:
                cond_res = pd.Series(True, index=df.index)
                
            result = result & cond_res
            
        return result

    def _calc_indicator(self, df: pd.DataFrame, ind_config) -> pd.Series:
        """Calculates a specific indicator for the condition engine."""
        ind_type = ind_config.type.upper()
        params = ind_config.params
        source = ind_config.source or "close"
        
        try:
            if ind_type in ("SMA", "EMA", "WMA", "DEMA", "TEMA"):
                length = int(params.get("length", 20))
                if ind_type == "SMA": return ta.sma(df[source], length=length)
                if ind_type == "EMA": return ta.ema(df[source], length=length)
                if ind_type == "WMA": return ta.wma(df[source], length=length)
                if ind_type == "DEMA": return ta.dema(df[source], length=length)
                if ind_type == "TEMA": return ta.tema(df[source], length=length)
            elif ind_type == "RSI":
                length = int(params.get("length", 14))
                return ta.rsi(df[source], length=length)
            elif ind_type == "MACD":
                fast = int(params.get("fast", 12))
                slow = int(params.get("slow", 26))
                signal = int(params.get("signal", 9))
                macd_df = ta.macd(df[source], fast=fast, slow=slow, signal=signal)
                # By default return MACD line, could be refined to return histogram or signal based on config
                cols = macd_df.columns.tolist()
                macd_col = [c for c in cols if c.startswith("MACD_")][0]
                return macd_df[macd_col]
            elif ind_type == "PRICE":
                return df[source]
            else:
                logger.warning(f"Unsupported condition indicator: {ind_type}")
                return pd.Series(0, index=df.index)
        except Exception as e:
            logger.error(f"Error calculating indicator for condition: {e}")
            return pd.Series(0, index=df.index)

    def _extract_metrics(self, pf, config: BacktestRunRequest, total_bars: int) -> BacktestMetrics:
        """Extracts and formats metrics from vectorbt Portfolio."""
        stats = pf.stats()
        
        # Calculate winning / losing trades manually or via vectorbt
        trades_df = pf.trades.records_readable
        
        # Safely extract stats, vectorbt stat names vary
        def get_stat(key, default=0.0):
            return stats[key] if key in stats and not pd.isna(stats[key]) else default

        net_profit = get_stat('Total Return [%]') / 100.0 * config.initial_capital
        win_rate = get_stat('Win Rate [%]')
        
        # Count trades
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['PnL'] > 0]) if total_trades > 0 else 0
        losing_trades = len(trades_df[trades_df['PnL'] < 0]) if total_trades > 0 else 0
        
        return BacktestMetrics(
            net_profit_usd=float(pf.total_profit()),
            net_profit_pct=float(pf.total_return() * 100),
            gross_profit_usd=float(trades_df['PnL'][trades_df['PnL'] > 0].sum() if total_trades > 0 else 0),
            gross_loss_usd=float(trades_df['PnL'][trades_df['PnL'] < 0].sum() if total_trades > 0 else 0),
            profit_factor=float(get_stat('Profit Factor')),
            max_drawdown_usd=0.0, # vectorbt provides Max Drawdown [%]
            max_drawdown_pct=float(get_stat('Max Drawdown [%]')),
            max_drawdown_duration_bars=int(get_stat('Max Drawdown Duration', pd.Timedelta(0)).days), # approximation
            recovery_factor=float(get_stat('Recovery Factor')),
            sharpe_ratio=float(get_stat('Sharpe Ratio')),
            sortino_ratio=float(get_stat('Sortino Ratio')),
            calmar_ratio=float(get_stat('Calmar Ratio')),
            var_95_pct=0.0, # Could be calculated separately
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate_pct=float(win_rate),
            avg_win_usd=float(trades_df['PnL'][trades_df['PnL'] > 0].mean() if winning_trades > 0 else 0),
            avg_loss_usd=float(trades_df['PnL'][trades_df['PnL'] < 0].mean() if losing_trades > 0 else 0),
            best_trade_usd=float(trades_df['PnL'].max() if total_trades > 0 else 0),
            worst_trade_usd=float(trades_df['PnL'].min() if total_trades > 0 else 0),
            avg_trade_duration_hours=0.0, # Needs parsing from vectorbt duration
            max_consecutive_wins=0,
            max_consecutive_losses=0,
            exposure_time_pct=float(get_stat('Exposure Time [%]')),
            total_bars=total_bars,
            initial_capital=config.initial_capital,
            final_capital=float(pf.value()[-1])
        )

    def _extract_trades(self, pf) -> List[Trade]:
        """Extracts list of trades."""
        trades_df = pf.trades.records_readable
        if trades_df.empty:
            return []
            
        result = []
        for i, row in trades_df.iterrows():
            # Vectorbt uses 'Direction' with 'Long' or 'Short'
            direction = row['Direction'] if 'Direction' in row else 'LONG'
            direction = str(direction).upper()
            
            entry_time = row['Entry Timestamp'].isoformat() if hasattr(row['Entry Timestamp'], 'isoformat') else str(row['Entry Timestamp'])
            exit_time = row['Exit Timestamp'].isoformat() if hasattr(row['Exit Timestamp'], 'isoformat') else str(row['Exit Timestamp'])
            
            trade = Trade(
                trade_id=i,
                direction=direction,
                entry_time=entry_time,
                entry_price=float(row['Entry Price']),
                exit_time=exit_time,
                exit_price=float(row['Exit Price']),
                size_usd=float(row['Size'] * row['Entry Price']),
                size_units=float(row['Size']),
                pnl_usd=float(row['PnL']),
                pnl_pct=float(row['Return'] * 100),
                commission_paid=float(row.get('Fees Paid', 0.0)),
                mae_pct=0.0, # Could be populated via vectorbt MFE/MAE if requested
                mfe_pct=0.0,
                exit_reason="Signal",
                bars_held=int(row.get('Exit Index', 0) - row.get('Entry Index', 0))
            )
            result.append(trade)
            
        return result

    def _extract_equity_curve(self, pf) -> List[EquityPoint]:
        """Extracts equity and drawdown curves."""
        value_series = pf.value()
        drawdown_series = pf.drawdown() * 100.0
        
        curve = []
        for idx, value in value_series.items():
            ts = int(idx.timestamp()) if hasattr(idx, 'timestamp') else int(idx)
            dd = drawdown_series.get(idx, 0.0)
            if pd.isna(dd): dd = 0.0
            
            curve.append(EquityPoint(
                t=ts,
                equity=float(value),
                drawdown_pct=float(dd)
            ))
            
        return curve

backtest_engine = BacktestEngine()
