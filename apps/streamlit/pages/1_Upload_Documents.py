import sys
from pathlib import Path
import streamlit as st
from modules.ingestion.infrastructure.chunkers import chunker_registry
from shared.domain.types import RunConfig
from shared.ai.embeddings import embedder_registry
from modules.ingestion.infrastructure.parsers.base import DEFAULT_STRATEGY_BY_EXTENSION
from modules.experiments.infrastructure.pipeline_orchestration import run_dataset_generation
from shared.retrieval import retriever_registry
from shared.infrastructure.storage.local_file_store import save_upload
from shared.ai.reranking import reranker_registry

sys.path.append(str(Path(__file__).resolve().parents[1]))
from lib import strategy_picker

st.set_page_config(page_title="Upload Documents - RAG-OS", page_icon="\U0001F4E4", layout="wide")
st.title("\U0001F4E4 Upload Documents & Create a Run")
st.markdown("Upload files, pick a strategy per stage, then click **Run pipeline**.")

run_name = st.text_input("Run name (optional)", value="")
uploaded_files = st.file_uploader("Upload documents", type=["pdf", "docx", "html", "htm", "txt", "md"], accept_multiple_files=True)

if uploaded_files:
    st.caption("Parser auto-detected per file:")
    for f in uploaded_files:
        ext = Path(f.name).suffix.lower()
        st.caption(f"- {f.name} -> `{DEFAULT_STRATEGY_BY_EXTENSION.get(ext, 'unsupported')}`")

st.subheader("Your decisions")
col1, col2, col3, col4 = st.columns(4)
with col1:
    chunker_name, chunker_params = strategy_picker("chunking", chunker_registry, "chunker")
with col2:
    embedder_name, embedder_params = strategy_picker("embedding", embedder_registry, "embedder")
with col3:
    retriever_name, retriever_params = strategy_picker("retrieval", retriever_registry, "retriever")
with col4:
    use_reranker = st.checkbox("Add a reranking stage", value=False)
    if use_reranker:
        reranker_name, reranker_params = strategy_picker("reranking", reranker_registry, "reranker")
    else:
        reranker_name, reranker_params = "", {}

if chunker_name == "semantic":
    st.info("Semantic chunking uses the embedder above and costs extra embedding calls.", icon="\u2139\ufe0f")

with st.expander("\U0001F4CB Review your run before executing", expanded=True):
    st.json({
        "chunker": {"name": chunker_name, "params": chunker_params},
        "embedder": {"name": embedder_name, "params": embedder_params},
        "retriever": {"name": retriever_name, "params": retriever_params},
        "reranker": {"name": reranker_name, "params": reranker_params} if reranker_name else None,
    })

st.divider()
if st.button("\u25b6\ufe0f Run pipeline", type="primary", disabled=not uploaded_files):
    config = RunConfig(name=run_name, parser_name="auto_by_extension", parser_params={},
                       chunker_name=chunker_name, chunker_params=chunker_params,
                       embedder_name=embedder_name, embedder_params=embedder_params,
                       retriever_name=retriever_name, retriever_params=retriever_params,
                       reranker_name=reranker_name, reranker_params=reranker_params)
    with st.spinner("Saving uploads..."):
        saved_paths = [save_upload(f.getvalue(), f.name, config.id) for f in uploaded_files]
    try:
        with st.spinner("Parsing -> chunking -> embedding -> indexing..."):
            run_row, documents, chunks, retriever, reranker = run_dataset_generation(saved_paths, config)
    except Exception as e:
        st.error(f"Pipeline failed: {e}")
    else:
        st.success(f"Run '{run_row.name or run_row.id}' created: {len(documents)} document(s), {len(chunks)} chunk(s).")
        st.info("Head to Parsing / Chunking / Embedding / Retrieval to inspect this run.", icon="\U0001F449")
