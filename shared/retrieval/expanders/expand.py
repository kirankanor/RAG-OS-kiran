from __future__ import annotations
from shared.retrieval.pipeline_context import PipelineContext
from shared.retrieval.pipeline_step import PipelineStep, pipeline_step_registry


@pipeline_step_registry.register("parent_document_expand", "Attaches each candidate's parent chunk as extra context.")
class ParentDocumentExpander(PipelineStep):
    name = "parent_document_expand"
    category = "expander"

    def run(self, ctx):
        chunks_by_id = ctx.chunks_by_id()
        for candidate in ctx.candidates:
            parent_id = candidate.chunk.parent_chunk_id
            if not parent_id:
                continue
            parent = chunks_by_id.get(parent_id)
            if parent is not None:
                candidate.parent_text = parent.text
        return ctx


@pipeline_step_registry.register("sentence_window_expand", "Attaches N neighboring chunks as extra context.")
class SentenceWindowExpander(PipelineStep):
    name = "sentence_window_expand"
    category = "expander"

    def __init__(self, window_size: int = 1):
        self.window_size = window_size

    def run(self, ctx):
        by_document = {}
        for chunk in ctx.all_chunks:
            by_document.setdefault(chunk.document_id, []).append(chunk)
        for doc_chunks in by_document.values():
            doc_chunks.sort(key=lambda c: c.position)
        for candidate in ctx.candidates:
            doc_chunks = by_document.get(candidate.chunk.document_id, [])
            try:
                idx = next(i for i, c in enumerate(doc_chunks) if c.id == candidate.chunk.id)
            except StopIteration:
                continue
            lo = max(0, idx - self.window_size)
            hi = min(len(doc_chunks), idx + self.window_size + 1)
            window_chunks = doc_chunks[lo:hi]
            candidate.parent_text = " ".join(c.text for c in window_chunks)
        return ctx
