from __future__ import annotations

import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field

from shared.infrastructure.logging.logger import get_logger

_log = get_logger("tracing")


@dataclass
class Span:
    name: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    attributes: dict[str, object] = field(default_factory=dict)
    duration_seconds: float = 0.0

    def set_attribute(self, key: str, value: object) -> None:
        self.attributes[key] = value


@contextmanager
def start_span(name: str, **attributes: object) -> Iterator[Span]:
    """Lightweight in-process span: logs start/end + duration. Not wired to an external
    tracing backend (OpenTelemetry, Jaeger, ...) -- swap the log call for a real exporter
    here once one is chosen, without touching call sites."""
    span = Span(name=name, attributes=dict(attributes))
    start = time.perf_counter()
    _log.info("span start: %s %s", span.name, span.attributes)
    try:
        yield span
    finally:
        span.duration_seconds = time.perf_counter() - start
        _log.info("span end: %s (%.3fs) %s", span.name, span.duration_seconds, span.attributes)
