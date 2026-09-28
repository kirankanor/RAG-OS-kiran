from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from modules.experiments.domain.entities.experiment_run import ExperimentRun
from modules.experiments.domain.models.experiment_config import ExperimentConfig, StrategyRef
from modules.experiments.domain.value_objects.experiment_id import ExperimentId
from modules.experiments.domain.value_objects.experiment_status import ExperimentStatus


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class Experiment:
    """Aggregate root: one config run across N pinned strategies (one ExperimentRun each)."""

    id: ExperimentId = field(default_factory=ExperimentId.new)
    name: str = ""
    description: str = ""
    config: ExperimentConfig = field(default_factory=ExperimentConfig)
    strategy_refs: list[StrategyRef] = field(default_factory=list)
    runs: list[ExperimentRun] = field(default_factory=list)
    status: ExperimentStatus = ExperimentStatus.PENDING
    created_at: str = field(default_factory=_utcnow)
    updated_at: str = field(default_factory=_utcnow)
    completed_at: str = ""

    def final_status(self) -> ExperimentStatus:
        """Status implied by run outcomes. Any failed run => FAILED (partial results kept)."""
        statuses = {r.status for r in self.runs}
        if ExperimentStatus.FAILED in statuses:
            return ExperimentStatus.FAILED
        if statuses <= {ExperimentStatus.COMPLETED}:
            return ExperimentStatus.COMPLETED
        if ExperimentStatus.CANCELLED in statuses:
            return ExperimentStatus.CANCELLED
        return self.status