from __future__ import annotations

import functools
import time
from collections.abc import Callable
from typing import TypeVar

from shared.infrastructure.logging.logger import get_logger
from shared.infrastructure.telemetry.metrics import metrics

_log = get_logger("instrumentation")
F = TypeVar("F", bound=Callable)


def instrument(name: str | None = None) -> Callable[[F], F]:
    """Decorator: counts calls/errors and records duration for the wrapped function via
    shared.infrastructure.telemetry.metrics, and logs exceptions before re-raising."""

    def decorator(fn: F) -> F:
        metric_name = name or f"{fn.__module__}.{fn.__qualname__}"

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            metrics.increment(f"{metric_name}.calls")
            try:
                return fn(*args, **kwargs)
            except Exception:
                metrics.increment(f"{metric_name}.errors")
                _log.exception("error in %s", metric_name)
                raise
            finally:
                metrics.set_gauge(f"{metric_name}.last_duration_seconds", time.perf_counter() - start)

        return wrapper  # type: ignore[return-value]

    return decorator
