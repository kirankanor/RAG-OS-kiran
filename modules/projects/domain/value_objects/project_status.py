from __future__ import annotations

from enum import Enum


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"  # read-only until unarchived
    DELETED = "deleted"    # soft delete
