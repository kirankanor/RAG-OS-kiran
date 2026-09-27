from modules.ingestion.infrastructure.chunkers import chunker_registry
from shared.domain.types import Document
from shared.ai.embeddings import embedder_registry
from modules.ingestion.infrastructure.parsers import parser_registry
from shared.retrieval import retriever_registry, pipeline_step_registry
from shared.ai.reranking import reranker_registry
from shared.ai.llm import generator_registry


def test_parser_registry_has_expected_strategies():
    names = parser_registry.names()
    for expected in ["txt_plain", "pdf_pymupdf", "pdf_pypdf", "docx_python_docx", "html_bs4"]:
        assert expected in names


def test_chunker_registry_has_expected_strategies():
    names = chunker_registry.names()
    for expected in ["fixed_size", "recursive_char", "sentence_window", "markdown_aware", "semantic", "code_aware"]:
        assert expected in names


def test_embedder_registry_has_expected_strategies():
    names = embedder_registry.names()
    for expected in ["local_minilm", "openai_text_embedding_3_small", "cohere_embed_v3"]:
        assert expected in names


def test_retriever_registry_has_expected_strategies():
    names = retriever_registry.names()
    for expected in ["faiss_flat_l2", "qdrant", "hybrid_bm25_vector"]:
        assert expected in names


def test_reranker_registry_has_expected_strategies():
    names = reranker_registry.names()
    for expected in ["cross_encoder", "cohere_rerank"]:
        assert expected in names


def test_pipeline_step_registry_has_expected_strategies():
    names = pipeline_step_registry.names()
    for expected in ["dense_flat", "dense_hnsw", "bm25", "qdrant_dense", "rrf_fuse", "weighted_fuse",
                      "metadata_filter", "parent_document_expand", "sentence_window_expand",
                      "mmr", "cross_encoder_rerank", "cohere_rerank"]:
        assert expected in names


def test_generator_registry_has_expected_strategies():
    names = generator_registry.names()
    assert "groq_chat" in names


def test_fixed_size_chunker_produces_chunks():
    chunker = chunker_registry.create("fixed_size", chunk_size=20, overlap=5)
    doc = Document(text="a" * 100)
    chunks = chunker.chunk(doc)
    assert len(chunks) > 1
    assert all(c.document_id == doc.id for c in chunks)


def test_recursive_char_chunker_respects_paragraphs():
    chunker = chunker_registry.create("recursive_char", chunk_size=50, overlap=0)
    doc = Document(text="First paragraph.\n\nSecond paragraph that is a bit longer than the first one.")
    chunks = chunker.chunk(doc)
    assert len(chunks) >= 2
