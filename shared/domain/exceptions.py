from __future__ import annotations


class DomainError(Exception):
    """Base exception for cross-cutting domain-layer errors (raise module-specific
    subclasses of this, or of Exception directly, in normal use)."""


class ConcurrencyError(DomainError):
    """Raised when an aggregate was saved from a stale version (optimistic locking)."""
