from __future__ import annotations

from enum import Enum


class DocumentStatus(str, Enum):
    ACTIVE = "active"
    DELETED = "deleted"  # soft delete: versions and files are kept
