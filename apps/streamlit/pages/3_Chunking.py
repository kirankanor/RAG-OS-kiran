import sys
from pathlib import Path
import streamlit as st
from sqlmodel import select
sys.path.append(str(Path(__file__).resolve().parents[1]))
from lib import run_picker
from shared.infrastructure.database.db_models import ChunkRow, get_session

st.set_page_config(page_title="Chunking - RAG-OS", page_icon="\u2702\ufe0f", layout="wide")
st.title("\u2702\ufe0f Chunking Inspector")
st.caption("See how a document was split, chunk boundaries, and size distribution.")

run = run_picker(key="chunking_run")
if run:
    st.markdown(f"**Chunker used:** `{run.chunker_name}`  -  params: `{run.chunker_params}`")
    with get_session() as session:
        chunks = list(session.exec(select(ChunkRow).where(ChunkRow.run_id == run.id).order_by(ChunkRow.position)))
    if not chunks:
        st.warning("No chunks found for this run.")
    else:
        lengths = [len(c.text) for c in chunks]
        col1, col2, col3 = st.columns(3)
        col1.metric("Total chunks", len(chunks))
        col2.metric("Avg chunk length (chars)", f"{sum(lengths) / len(lengths):.0f}")
        col3.metric("Min / Max length", f"{min(lengths)} / {max(lengths)}")
        st.bar_chart(lengths)
        for chunk in chunks:
            label = f"#{chunk.position}  -  {len(chunk.text)} chars  -  chars[{chunk.char_start}:{chunk.char_end}]"
            with st.expander(label):
                st.write(chunk.text)
