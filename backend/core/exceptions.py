"""Custom exception classes matching the error codes defined in STAGE 6.1."""

from typing import Any, Dict, Optional


class BacktestProException(Exception):
    """Base exception for all BacktestPro errors."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class SymbolNotFoundException(BacktestProException):
    def __init__(self, symbol: str):
        super().__init__(
            code="SYMBOL_NOT_FOUND",
            message=f"El símbolo '{symbol}' no fue encontrado en ninguna fuente de datos.",
            status_code=404,
        )


class DataFetchError(BacktestProException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code="DATA_FETCH_ERROR",
            message=message,
            status_code=502,
            details=details,
        )


class InsufficientDataError(BacktestProException):
    def __init__(self, message: str):
        super().__init__(
            code="INSUFFICIENT_DATA",
            message=message,
            status_code=422,
        )


class BacktestNotFoundException(BacktestProException):
    def __init__(self, job_id: str):
        super().__init__(
            code="BACKTEST_NOT_FOUND",
            message=f"El backtest con ID '{job_id}' no fue encontrado.",
            status_code=404,
        )


class StrategyInvalidError(BacktestProException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code="STRATEGY_INVALID",
            message=message,
            status_code=422,
            details=details,
        )


class StrategyRuntimeError(BacktestProException):
    def __init__(self, message: str):
        super().__init__(
            code="STRATEGY_RUNTIME_ERROR",
            message=message,
            status_code=422,
        )


class UnauthorizedError(BacktestProException):
    def __init__(self, message: str = "Token inválido o ausente."):
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            status_code=401,
        )


class JobAlreadyRunningError(BacktestProException):
    def __init__(self):
        super().__init__(
            code="JOB_ALREADY_RUNNING",
            message="Ya hay un backtest corriendo para este usuario.",
            status_code=409,
        )


class InternalError(BacktestProException):
    def __init__(self, message: str = "Error inesperado del servidor."):
        super().__init__(
            code="INTERNAL_ERROR",
            message=message,
            status_code=500,
        )
