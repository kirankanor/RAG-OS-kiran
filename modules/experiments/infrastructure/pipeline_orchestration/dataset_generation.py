from __future__ import annotations
from pathlib import Path
from modules.ingestion.infrastructure.chunkers import chunker_registry
from modules.ingestion.infrastructure.chunkers.semantic import SemanticChunker
from shared.domain.types import Chunk, Document, RunConfig
from shared.ai.embeddings import embedder_registry
from modules.ingestion.infrastructure.parsers import parser_for_file
from shared.retrieval import retriever_registry
from shared.retrieval.legacy_base import Retriever
from shared.infrastructure.database.db_models import ChunkRow, DocumentRow, EmbeddingRow, RunRow, dumps, get_session
from shared.ai.reranking import reranker_registry
from shared.ai.reranking.base import Reranker


def run_dataset_generation(file_paths, config: RunConfig):
    embedder = embedder_registry.create(config.embedder_name, **config.embedder_params)
    if config.chunker_name == "semantic":
        chunker = SemanticChunker(embed_fn=embedder.embed, **config.chunker_params)
    else:
        chunker = chunker_registry.create(config.chunker_name, **config.chunker_params)
    retriever = retriever_registry.create(config.retriever_name, **config.retriever_params)
    documents = [parser_for_file(fp).parse(fp) for fp in file_paths]
    all_chunks = []
    for doc in documents:
        all_chunks.extend(chunker.chunk(doc))
    vectors = embedder.embed([c.text for c in all_chunks]) if all_chunks else []
    retriever.build(all_chunks, vectors)
    reranker = reranker_registry.create(config.reranker_name, **config.reranker_params) if config.reranker_name else None
    _persist_run(config, documents, all_chunks, vectors)
    return _run_row(config), documents, all_chunks, retriever, reranker


def _run_row(config):
    return RunRow(id=config.id, name=config.name, parser_name=config.parser_name,
                  parser_params=dumps(config.parser_params), chunker_name=config.chunker_name,
                  chunker_params=dumps(config.chunker_params), embedder_name=config.embedder_name,
                  embedder_params=dumps(config.embedder_params), retriever_name=config.retriever_name,
                  retriever_params=dumps(config.retriever_params), reranker_name=config.reranker_name,
                  reranker_params=dumps(config.reranker_params), created_at=config.created_at)


def _persist_run(config, documents, chunks, vectors):
    with get_session() as session:
        session.add(_run_row(config))
        for doc in documents:
            session.add(DocumentRow(id=doc.id, run_id=config.id, source_filename=doc.source_filename,
                                     text=doc.text, metadata_json=dumps(doc.metadata),
                                     parser_name=doc.parser_name, created_at=doc.created_at))
        for chunk, vector in zip(chunks, vectors):
            session.add(ChunkRow(id=chunk.id, run_id=config.id, document_id=chunk.document_id,
                                  text=chunk.text, position=chunk.position, char_start=chunk.char_start,
                                  char_end=chunk.char_end, metadata_json=dumps(chunk.metadata),
                                  chunker_name=chunk.chunker_name))
            session.add(EmbeddingRow(id=f"{chunk.id}_emb", run_id=config.id, chunk_id=chunk.id,
                                      vector_json=dumps(vector), dim=len(vector),
                                      embedder_name=config.embedder_name))
        session.commit()
