from __future__ import annotations

from enum import Enum


class ArtifactType(str, Enum):
    REPORT = "report"    # markdown report (e.g. on a decision)
    CODE = "code"        # runnable script reproducing a strategy
    PACKAGE = "package"  # zip bundle of a project's results
