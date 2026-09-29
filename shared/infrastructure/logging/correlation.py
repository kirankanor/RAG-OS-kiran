from __future__ import annotations

import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> str | None:
    return _correlation_id.get()


def new_correlation_id() -> str:
    return uuid.uuid4().hex[:12]


@contextmanager
def correlation_scope(correlation_id: str | None = None) -> Iterator[str]:
    """Binds a correlation id (generating one if omitted) for the duration of the `with`
    block, so every log record and downstream call within it can be tied together.
    Nested scopes restore the outer id on exit."""
    cid = correlation_id or new_correlation_id()
    token = _correlation_id.set(cid)
    try:
        yield cid
    finally:
        _correlation_id.reset(token)
