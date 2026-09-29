from __future__ import annotations

from dataclasses import dataclass, field

from shared.domain.domain_event import DomainEvent
from shared.domain.entity import Entity


@dataclass
class AggregateRoot(Entity):
    """Entity that queues domain events instead of persisting them, mirroring the
    `pending_events` + `pull_events()` pattern already used by Project and Document.
    Optional base for new aggregates; existing ones keep their own hand-written version."""

    pending_events: list[DomainEvent] = field(default_factory=list, repr=False, compare=False)

    def raise_event(self, event: DomainEvent) -> None:
        self.pending_events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        events, self.pending_events = self.pending_events, []
        return events
