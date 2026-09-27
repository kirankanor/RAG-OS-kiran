from __future__ import annotations

from abc import ABC, abstractmethod

from shared.domain.registry import Registry
from shared.retrieval.pipeline_context import PipelineContext


class PipelineStep(ABC):
    name: str = "base"
    category: str = "base"

    @abstractmethod
    def run(self, ctx: PipelineContext) -> PipelineContext:
        raise NotImplementedError


pipeline_step_registry: Registry[PipelineStep] = Registry("pipeline_step")
