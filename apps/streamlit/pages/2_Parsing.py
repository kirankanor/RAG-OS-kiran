import sys
from pathlib import Path
import streamlit as st
from sqlmodel import select
sys.path.append(str(Path(__file__).resolve().parents[1]))
from lib import run_picker
from shared.infrastructure.database.db_models import DocumentRow, get_session, loads

st.set_page_config(page_title="Parsing - RAG-OS", page_icon="\U0001F4C4", layout="wide")
st.title("\U0001F4C4 Parsing Inspector")
st.caption("See exactly what text a parser extracted from each uploaded file.")

run = run_picker(key="parsing_run")
if run:
    st.markdown(f"**Parser used:** `{run.parser_name}`")
    with get_session() as session:
        documents = list(session.exec(select(DocumentRow).where(DocumentRow.run_id == run.id)))
    if not documents:
        st.warning("No documents found for this run.")
    for doc in documents:
        metadata = loads(doc.metadata_json)
        with st.expander(f"\U0001F4CE {doc.source_filename}  -  {len(doc.text):,} chars"):
            st.json(metadata)
            st.text_area("Parsed text", value=doc.text, height=400, key=f"doc_{doc.id}")
