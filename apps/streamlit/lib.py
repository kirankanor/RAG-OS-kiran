from __future__ import annotations
import json
import streamlit as st
from shared.domain.types import RunConfig
from modules.experiments.infrastructure.pipeline_orchestration.run_manager import load_retriever_for_run
from shared.infrastructure.database.db_models import RunRow, list_runs, loads

EXAMPLE_PARAMS: dict[str, dict] = {
    "code_aware": {"max_chunk_size": 1500},
    "fixed_size": {"chunk_size": 1000, "overlap": 100},
    "recursive_char": {"chunk_size": 1000, "overlap": 150},
    "sentence_window": {"sentences_per_chunk": 5, "sentence_overlap": 1},
    "markdown_aware": {"max_chunk_size": 1200},
    "semantic": {"similarity_threshold": 0.65, "max_chunk_size": 2000},
    "local_minilm": {"model_name": "sentence-transformers/all-MiniLM-L6-v2"},
    "openai_text_embedding_3_small": {"model": "text-embedding-3-small"},
    "cohere_embed_v3": {"model": "embed-english-v3.0"},
    "faiss_flat_l2": {},
    "qdrant": {"collection_name": "rag_os_experiment", "url": "http://localhost:6333"},
    "hybrid_bm25_vector": {"alpha": 0.5, "fusion_method": "rrf", "rrf_k": 60},
    "cross_encoder": {"model_name": "cross-encoder/ms-marco-MiniLM-L-6-v2"},
    "cohere_rerank": {"model": "rerank-english-v3.0"},
}

def run_label(run: RunRow) -> str:
    display_name = run.name or run.id
    return f"{display_name} - {run.parser_name} / {run.chunker_name} / {run.embedder_name} / {run.retriever_name}"


def run_picker(key: str) -> RunRow | None:
    runs = list_runs()
    if not runs:
        st.warning("No runs yet. Create one on the **Upload Documents** page first.")
        return None
    return st.selectbox("Choose a run", options=runs, format_func=run_label, key=key)


def strategy_picker(kind: str, registry, key_prefix: str):
    names = registry.names()
    if not names:
        st.error(f"No {kind} strategies registered.")
        return "", {}
    name = st.selectbox(f"{kind.capitalize()} strategy", options=names, key=f"{key_prefix}_name",
                         help=registry.description(names[0]))
    st.caption(registry.description(name))
    example = json.dumps(EXAMPLE_PARAMS.get(name, {}), indent=2)
    params_raw = st.text_area(f"{kind.capitalize()} params (JSON)", value=example,
                               key=f"{key_prefix}_{name}_params", help="Prefilled with example values.")
    try:
        params = json.loads(params_raw) if params_raw.strip() else {}
    except json.JSONDecodeError:
        st.error(f"{kind.capitalize()} params must be valid JSON. Using {{}} instead.")
        params = {}
    return name, params


@st.cache_resource(show_spinner="Loading retriever for this run...")
def get_cached_retriever_and_reranker(run_id: str):
    return load_retriever_for_run(run_id)


def config_from_run(run: RunRow) -> RunConfig:
    return RunConfig(id=run.id, name=run.name, parser_name=run.parser_name,
                      parser_params=loads(run.parser_params), chunker_name=run.chunker_name,
                      chunker_params=loads(run.chunker_params), embedder_name=run.embedder_name,
                      embedder_params=loads(run.embedder_params), retriever_name=run.retriever_name,
                      retriever_params=loads(run.retriever_params), reranker_name=run.reranker_name,
                      reranker_params=loads(run.reranker_params), created_at=run.created_at)
