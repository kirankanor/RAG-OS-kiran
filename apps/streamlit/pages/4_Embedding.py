import sys
from pathlib import Path
import streamlit as st
from sqlmodel import select
sys.path.append(str(Path(__file__).resolve().parents[1]))
from lib import run_picker
from shared.infrastructure.database.db_models import ChunkRow, EmbeddingRow, get_session, loads

st.set_page_config(page_title="Embedding - RAG-OS", page_icon="\U0001F9EE", layout="wide")
st.title("\U0001F9EE Embedding Inspector")
st.caption("Check embedding dimensionality and preview raw vectors per chunk.")

run = run_picker(key="embedding_run")
if run:
    st.markdown(f"**Embedder used:** `{run.embedder_name}`  -  params: `{run.embedder_params}`")
    with get_session() as session:
        embeddings = list(session.exec(select(EmbeddingRow).where(EmbeddingRow.run_id == run.id)))
        chunk_text_by_id = {c.id: c.text for c in session.exec(select(ChunkRow).where(ChunkRow.run_id == run.id))}
    if not embeddings:
        st.warning("No embeddings found for this run.")
    else:
        dims = {e.dim for e in embeddings}
        col1, col2 = st.columns(2)
        col1.metric("Total vectors", len(embeddings))
        col2.metric("Dimension", ", ".join(str(d) for d in dims))
        st.subheader("Sample vectors")
        n_preview = min(10, len(embeddings))
        for emb in embeddings[:n_preview]:
            vector = loads(emb.vector_json)
            preview_text = chunk_text_by_id.get(emb.chunk_id, "")[:80]
            with st.expander(f"chunk `{emb.chunk_id}` - \"{preview_text}...\""):
                st.write(f"First 8 dimensions: {vector[:8]}")
