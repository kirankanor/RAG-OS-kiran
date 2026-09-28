from __future__ import annotations

from modules.experiments.application.services.experiment_service import ExperimentService
from modules.experiments.domain.entities.experiment import Experiment
from modules.experiments.domain.exceptions import ExperimentStateError
from modules.experiments.domain.interfaces.experiment_runner import experiment_runner_registry
from modules.experiments.domain.value_objects.experiment_status import ExperimentStatus
from modules.experiments.infrastructure.execution.local_executor import ExecutionResult, LocalExecutor
from modules.strategies.domain.exceptions import StrategyError


class ExperimentOrchestrator:
    """Runs an experiment's strategies sequentially. A failed run does not stop the others;
    stop() is honoured between runs."""

    def __init__(self, service: ExperimentService | None = None, executor: LocalExecutor | None = None):
        self.service = service or ExperimentService()
        self.executor = executor or LocalExecutor()

    def run(self, experiment_id: str) -> Experiment:
        repo = self.service.repository
        experiment = self.service.get(experiment_id)
        if experiment.status != ExperimentStatus.PENDING:
            raise ExperimentStateError(
                f"Experiment is {experiment.status.value}; only pending experiments can run.")
        runner = experiment_runner_registry.create(experiment.config.runner)
        repo.set_status(experiment_id, ExperimentStatus.RUNNING)

        for run in experiment.runs:
            if repo.get_status(experiment_id) == ExperimentStatus.CANCELLED:
                break
            run.start()
            repo.save_run(run)
            try:
                strategy = self.service.strategies.get(run.strategy_id, run.strategy_version)
                outcome = self.executor.execute(runner, experiment.config, strategy)
            except StrategyError as e:
                outcome = ExecutionResult(False, error=str(e))
            if outcome.ok:
                run.complete(outcome.result, outcome.duration_seconds)
            else:
                run.fail(outcome.error, outcome.duration_seconds)
            repo.save_run(run)

        final = self.service.get(experiment_id)  # fresh: stop() may have changed it
        if final.status != ExperimentStatus.CANCELLED:
            repo.set_status(experiment_id, final.final_status())
        return self.service.get(experiment_id)