from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any

from shared.domain.domain_event import DomainEvent
from shared.infrastructure.logging.logger import get_logger

_log = get_logger("events")
Handler = Callable[[Any], None]


class InMemoryEventBus:
    """Synchronous pub/sub for domain events, keyed by event class. Suitable as the
    `publisher` callable every module's *Service constructor already accepts
    (e.g. ProjectService(publisher=...)). Swap for shared.infrastructure.queue.celery /
    redis to go async without changing publisher call sites."""

    def __init__(self) -> None:
        self._handlers: dict[type, list[Handler]] = defaultdict(list)

    def subscribe(self, event_type: type[DomainEvent], handler: Handler) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, event: DomainEvent) -> None:
        for handler in self._handlers.get(type(event), []):
            try:
                handler(event)
            except Exception:  # noqa: BLE001 - one bad handler must not sink the others
                _log.exception("event handler failed for %s", type(event).__name__)


event_bus = InMemoryEventBus()
