from __future__ import annotations

from collections.abc import Callable

from modules.ingestion.infrastructure.chunkers.base import Chunker, chunker_registry
from modules.ingestion.infrastructure.chunkers.recursive_char import RecursiveCharacterChunker

LlmFn = Callable[[str], str]
_PROMPT_TEMPLATE = (
    "Document:\n{doc}\n\nHere is a chunk from this document:\n{chunk}\n\n"
    "Give a short (1-2 sentence) context describing where this chunk fits in the "
    "overall document, to improve search retrieval. Answer only with the context."
)


@chunker_registry.register("contextual", "Prepends an LLM-generated context summary to each chunk.")
class ContextualChunker(Chunker):
    name = "contextual"

    def __init__(self, llm_fn=None, chunk_size: int = 1000, overlap: int = 150):
        self.llm_fn = llm_fn
        self._base = RecursiveCharacterChunker(chunk_size=chunk_size, overlap=overlap)

    def chunk(self, document):
        if self.llm_fn is None:
            raise ValueError("ContextualChunker requires an llm_fn.")
        base_chunks = self._base.chunk(document)
        for c in base_chunks:
            prompt = _PROMPT_TEMPLATE.format(doc=document.text[:8000], chunk=c.text)
            context = self.llm_fn(prompt).strip()
            c.text = f"{context}\n\n{c.text}"
            c.chunker_name = self.name
            c.metadata["prepended_context"] = context
        return base_chunks
