from __future__ import annotations

import threading
from collections import defaultdict


class MetricsRegistry:
    """In-process counters/gauges. Not wired to an external metrics backend (Prometheus,
    StatsD, ...) -- swap the storage here for a real exporter once one is chosen."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, float] = defaultdict(float)
        self._gauges: dict[str, float] = {}

    def increment(self, name: str, value: float = 1.0, **tags: str) -> None:
        with self._lock:
            self._counters[self._key(name, tags)] += value

    def set_gauge(self, name: str, value: float, **tags: str) -> None:
        with self._lock:
            self._gauges[self._key(name, tags)] = value

    def snapshot(self) -> dict[str, dict[str, float]]:
        with self._lock:
            return {"counters": dict(self._counters), "gauges": dict(self._gauges)}

    @staticmethod
    def _key(name: str, tags: dict[str, str]) -> str:
        suffix = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}{{{suffix}}}" if suffix else name


metrics = MetricsRegistry()
