from __future__ import annotations

from modules.experiments.infrastructure.execution.local_executor import ExecutionResult


class SandboxExecutor:
    """Stub. Same execute() signature as LocalExecutor; intended for subprocess/container isolation."""

    def execute(self, runner, config, strategy) -> ExecutionResult:
        raise NotImplementedError("Sandboxed execution is not implemented yet.")