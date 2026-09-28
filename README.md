# RAG-OS-kiran

## rag-strategy-engine — folder-structure skeleton

This is the target DDD modular-monolith layout, generated for your RAG-OS project.
See RESTRUCTURE_NOTES.md for exactly what's real, what's a stub, and what to fix
before deleting the compatibility shim.

# rag-strategy-engine

RAG-OS, restructured into a DDD modular-monolith layout. The pipeline
(parsing → chunking → embedding → retrieval → reranking → generation) is
working code moved over from the original `rag_os` package; everything else
in `modules/` beyond that is still a stub — see **Status** below.

## Requirements

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
# base install (streamlit app + core pipeline, no ML backends)
uv sync

# add local backends (faiss, pymupdf, rank-bm25, sentence-transformers)
uv sync --extra local

# add cloud backends (cohere, openai, qdrant-client, groq)
uv sync --extra cloud

# both
uv sync --extra local --extra cloud
```

`uv sync` reads `[project.dependencies]` / `[project.optional-dependencies]`
in `pyproject.toml` and creates `.venv` automatically. There's no committed
`uv.lock` yet — run `uv lock` once and commit it so everyone resolves the
same versions.

Copy `.env.example` to `.env` and fill in whatever your configured backends
need (API keys, DB URL, etc.) — see `shared/config/settings.py` for what's
read.

## Running things

```bash
# Streamlit app
uv run streamlit run apps/streamlit/Home.py

# tests
uv run pytest

# a single test file
uv run pytest tests/unit/test_registries_legacy.py -v

# any one-off script
uv run python scripts/seed_data.py
```

`uv run` uses the synced `.venv` without you needing to activate it.

## Layout

```
modules/<domain>/{domain,application,infrastructure,presentation}
    evaluation, projects, ingestion, experiments, strategies,
    corpus_analysis, decisions, artifacts, users, documents

shared/
    ai/{embeddings,llm,reranking}   — model-backed building blocks
    retrieval/                      — the retrieval pipeline engine
    domain/                         — cross-cutting types (Document, Chunk,
                                      RetrievalResult, RunConfig, Registry)
    config/, infrastructure/

apps/
    streamlit/  — working UI, wraps the pipeline above
    api/        — FastAPI, stub
    worker/     — Celery, stub
```

See `RESTRUCTURE_NOTES.md` for the full old-path → new-path mapping and the
reasoning behind each placement decision.

## Status
**Working today:** ingestion (parsing/normalization/chunking with tracked runs),
users (register/auth/JWT/organizations), strategies (saved, versioned configs),
experiments (run N strategies over the same files/queries), evaluation (datasets,
recall/precision/MRR/nDCG, comparison), corpus_analysis (once phase 6 is applied),
plus embeddings, retrieval, reranking, generation and the Streamlit app.

**Not yet built:** decisions, documents, projects, artifacts, the LLM-based
evaluation metrics and the ragas/deepeval adapters, shared cross-cutting
infrastructure, apps/api, apps/worker, migrations, scripts.

**Untested:** the `local` and `cloud` extras haven't been exercised
end-to-end yet (those deps are lazily imported inside method bodies). Run
`uv sync --extra local --extra cloud` and drive a real ingest → retrieve →
rerank flow through the Streamlit app before trusting that path fully.