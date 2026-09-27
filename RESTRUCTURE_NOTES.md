# What's in this skeleton

**472 stub files** (one-line `"""TODO: not yet implemented..."""`) for every
path in the target architecture doc — `modules/*/domain,application,infrastructure,presentation`,
`shared/*`, `apps/*`, `tests/*`, `docs/*`, `migrations/*`, `docker/*`.

**Your actual working code, moved:**

| Old location (rag_os) | New location |
|---|---|
| `ingestion/parsing/*` | `modules/ingestion/infrastructure/parsers/*` |
| `ingestion/chunking/*` | `modules/ingestion/infrastructure/chunkers/*` (doc doesn't define this folder — added to match `parsers/`) |
| `ingestion/embedding/*` | `shared/ai/embeddings/*` (doc's own home for embedding impls) |
| `generation/groq_chat.py` | `shared/ai/llm/groq.py` |
| `retrieval/rerankers/{cross_encoder,cohere_rerank}.py` | `shared/ai/reranking/*` |
| `retrieval/{pipeline_context,pipeline_step,pipeline_runner,base,faiss_local,qdrant_cloud,hybrid_bm25_vector}.py` + `generators/`, `fusers/`, `filters/`, `expanders/`, `mmr.py`, `existing_rerankers_adapter.py` | `shared/retrieval/*` — **the doc has no home for this**, see the note inside `shared/retrieval/__init__.py`; flag for your review |
| `database/db.py`, `file_store.py` | `shared/infrastructure/database/db_models.py`, `shared/infrastructure/storage/local_file_store.py` |
| `pipeline/dataset_generation.py`, `run_manager.py` | `modules/experiments/infrastructure/pipeline_orchestration/*` |
| `evaluation/*` | `modules/evaluation/infrastructure/{manual_review,metrics}/*` |
| `config/settings.py` | `shared/config/settings.py` |
| `app/*` (Streamlit) | `apps/streamlit/*` — unchanged, kept per your decision |
| `tests/test_registries.py` | `tests/unit/test_registries_legacy.py` |

**`shared/rag_os_compat/rag_os/`** — your entire original package, copied byte-for-byte,
untouched imports, fully working. `apps/streamlit/*` still imports from here
(`from rag_os...`), so **the app runs today, exactly as before.**

# What's NOT done yet

The files moved into `modules/` and `shared/ai`, `shared/retrieval` above **still
say `from rag_os.xxx import ...` internally** — I did not rewrite their imports,
because that requires deciding the final package roots first (do `modules/` and
`shared/` become importable as `modules.xxx` / `shared.xxx`, added to
`pyproject.toml` `[tool.setuptools] packages`, or do you add `src/` back?).

When you're ready to cut over from `rag_os_compat` to the split files:

1. Add `modules` and `shared` as installable packages (extend `pyproject.toml`).
2. In every moved file, replace:
   - `from rag_os.core...` → `from shared.rag_os_compat.rag_os.core...` (or wherever `core/types.py` + `registry.py` finally live — consider moving `core` itself to `shared/domain/` since it's the one truly cross-cutting piece)
   - `from rag_os.ingestion...` → `from modules.ingestion.infrastructure...`
   - `from rag_os.retrieval...` → `from shared.retrieval...`
   - `from rag_os.generation...` → `from shared.ai.llm...`
3. Repoint `apps/streamlit/*.py` imports the same way, then delete `shared/rag_os_compat/`.
4. Everything else (`projects`, `documents`, `corpus_analysis`, `strategies`, `experiments`
   business logic, `evaluation` beyond the moved metrics, `decisions`, `artifacts`, `users`,
   `apps/api`, `apps/worker`) is genuinely new code — none of it existed in rag_os.

# Decisions I made that you should confirm

- `chunkers/` folder under `ingestion/infrastructure/` — invented, doc only listed `parsers/`.
- `shared/retrieval/` — invented, doc has no slot for the retrieval pipeline engine.
- `shared/ai/embeddings/huggingface.py` = your `local_minilm` (sentence-transformers) embedder — doc's tree says "huggingface.py", closest match.
- Kept `apps/streamlit/` (not in the doc's tree, which only has `apps/api` + `apps/worker` for FastAPI/Celery) since you're keeping Streamlit.

# Cutover complete

The import rewiring above is done and `shared/rag_os_compat/` has been deleted.

What changed from the plan above:
- **`core/types.py` and `core/registry.py` moved to `shared/domain/types.py` and
  `shared/domain/registry.py`.** This was the one open question — deleting the
  compat shim required giving `core` a real home, so this call got made rather
  than left blocking. Every `from rag_os.core...` import now points there.
- `pipeline_runner.py`'s old `from rag_os.retrieval import ... rerankers` bag
  import got split: `from shared.retrieval import expanders, filters, fusers,
  generators, mmr, reranker_pipeline_adapters` + `from shared.ai.reranking import
  cross_encoder, cohere` — the old `rerankers` package's contents ended up split
  across those two destinations, so no single bag import covers it anymore.
- `modules/ingestion/infrastructure/parsers/__init__.py` was still referencing
  the pre-rename submodule names (`pdf_pymupdf`, `pdf_pypdf`) after the files
  themselves were renamed to `pymupdf_parser.py` / `pypdf_parser.py`. Fixed.
- Added two `__init__.py` files that were missing from the invented folders
  (`pipeline_orchestration/`, `manual_review/`) — needed for `modules.experiments
  .infrastructure.pipeline_orchestration` to work as a package with a bag import.
- Removed a stray empty directory literally named
  `{generators,fusers,filters,expanders}` — leftover from an unexpanded shell
  brace-glob during scaffolding.
- `pyproject.toml`'s `[tool.setuptools]` now uses `packages.find` over
  `modules*`, `shared*`, `apps*` instead of pointing at the deleted compat shim.

Verified: every real (non-stub) module byte-compiles and imports cleanly in a
fresh venv, `tests/unit/test_registries_legacy.py` passes (9/9), and all 6
Streamlit pages execute their top-level code without error.

