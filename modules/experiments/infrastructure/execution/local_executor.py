from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from modules.experiments.domain.interfaces.experiment_runner import ExperimentRunner
from modules.experiments.domain.models.experiment_config import ExperimentConfig
from modules.strategies.domain.entities.strategy import Strategy


@dataclass
class ExecutionResult:
    ok: bool
    result: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    duration_seconds: float = 0.0


class LocalExecutor:
    """Runs a runner in-process. Any exception becomes a failed ExecutionResult."""

    def execute(self, runner: ExperimentRunner, config: ExperimentConfig,
                strategy: Strategy) -> ExecutionResult:
        start = time.perf_counter()
        try:
            result = runner.run(config, strategy)
        except Exception as e:  # noqa: BLE001 - a bad strategy must not abort the experiment
            return ExecutionResult(False, error=f"{type(e).__name__}: {e}",
                                   duration_seconds=time.perf_counter() - start)
        return ExecutionResult(True, result=result, duration_seconds=time.perf_counter() - start)