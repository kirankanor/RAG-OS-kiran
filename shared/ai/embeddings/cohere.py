from __future__ import annotations
import os
from shared.ai.embeddings.base import Embedder, embedder_registry


@embedder_registry.register("cohere_embed_v3", "Cohere embed-english-v3.0. Requires COHERE_API_KEY.")
class CohereEmbedder(Embedder):
    name = "cohere_embed_v3"

    def __init__(self, model: str = "embed-english-v3.0", api_key: str | None = None):
        import cohere
        key = api_key or os.environ.get("COHERE_API_KEY")
        if not key:
            raise ValueError("No Cohere API key found.")
        self.model = model
        self._client = cohere.Client(key)
        self.dim = 1024

    def embed(self, texts):
        response = self._client.embed(texts=texts, model=self.model, input_type="search_document")
        return list(response.embeddings)

    def embed_query(self, query):
        response = self._client.embed(texts=[query], model=self.model, input_type="search_query")
        return next(iter(response.embeddings))
