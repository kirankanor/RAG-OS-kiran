from __future__ import annotations
from shared.ai.embeddings.base import Embedder, embedder_registry


@embedder_registry.register("local_minilm", "Local sentence-transformers model. Requires 'local' extra.")
class LocalMiniLmEmbedder(Embedder):
    name = "local_minilm"

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model_name = model_name
        self._model = SentenceTransformer(model_name)
        self.dim = self._model.get_sentence_embedding_dimension()

    def embed(self, texts):
        vectors = self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return vectors.tolist()
