from __future__ import annotations

from modules.experiments.application.services.experiment_orchestrator import ExperimentOrchestrator
from modules.experiments.domain.entities.experiment import Experiment


class RunExperimentCommand:
    """Runs synchronously and returns the finished experiment."""

    def __init__(self, orchestrator: ExperimentOrchestrator | None = None):
        self.orchestrator = orchestrator or ExperimentOrchestrator()

    def execute(self, experiment_id: str) -> Experiment:
        return self.orchestrator.run(experiment_id)