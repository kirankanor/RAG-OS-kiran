from __future__ import annotations
import os
from shared.ai.embeddings.base import Embedder, embedder_registry


@embedder_registry.register("openai_text_embedding_3_small", "OpenAI text-embedding-3-small. Requires OPENAI_API_KEY.")
class OpenAiEmbedder(Embedder):
    name = "openai_text_embedding_3_small"

    def __init__(self, model: str = "text-embedding-3-small", api_key: str | None = None):
        from openai import OpenAI
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise ValueError("No OpenAI API key found.")
        self.model = model
        self._client = OpenAI(api_key=key)
        self.dim = 1536 if model == "text-embedding-3-small" else 3072

    def embed(self, texts):
        response = self._client.embeddings.create(model=self.model, input=texts)
        return [item.embedding for item in response.data]
