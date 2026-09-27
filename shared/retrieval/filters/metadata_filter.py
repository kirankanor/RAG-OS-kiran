from __future__ import annotations
from typing import Any
from shared.retrieval.pipeline_context import PipelineContext
from shared.retrieval.pipeline_step import PipelineStep, pipeline_step_registry


@pipeline_step_registry.register("metadata_filter", "Drops candidates whose Chunk.metadata doesn't match filters.")
class MetadataFilter(PipelineStep):
    name = "metadata_filter"
    category = "filter"

    def __init__(self, equals=None, gte=None, lte=None):
        self.equals = equals or {}
        self.gte = gte or {}
        self.lte = lte or {}

    def _passes(self, metadata):
        for key, value in self.equals.items():
            if metadata.get(key) != value:
                return False
        for key, value in self.gte.items():
            if key not in metadata or metadata[key] < value:
                return False
        for key, value in self.lte.items():
            if key not in metadata or metadata[key] > value:
                return False
        return True

    def run(self, ctx):
        if not (self.equals or self.gte or self.lte):
            return ctx
        ctx.candidates = [c for c in ctx.candidates if self._passes(c.chunk.metadata)]
        return ctx
