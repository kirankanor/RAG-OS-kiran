from __future__ import annotations

import logging
import sys
from functools import lru_cache

from shared.infrastructure.logging.correlation import get_correlation_id

_FORMAT = "%(asctime)s %(levelname)s [%(correlation_id)s] %(name)s: %(message)s"


class _CorrelationFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = get_correlation_id() or "-"
        return True


@lru_cache
def _configure_root() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT))
    handler.addFilter(_CorrelationFilter())
    root = logging.getLogger("rag_os")
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    root.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Logger under the 'rag_os' namespace; every record carries the current
    correlation id (see shared.infrastructure.logging.correlation)."""
    _configure_root()
    return logging.getLogger(f"rag_os.{name}")
