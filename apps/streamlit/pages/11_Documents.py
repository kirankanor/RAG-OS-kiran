import sys
from pathlib import Path
import streamlit as st
sys.path.append(str(Path(__file__).resolve().parents[1]))

from modules.documents.application.commands.create_version import CreateVersionCommand
from modules.documents.application.commands.delete_document import DeleteDocumentCommand
from modules.documents.application.commands.upload_document import UploadDocumentCommand
from modules.documents.application.queries.list_documents import ListDocumentsQuery
from modules.documents.domain.exceptions import DocumentError

st.set_page_config(page_title="Documents - RAG-OS", page_icon="\U0001F4C1", layout="wide")
st.title("\U0001F4C1 Documents")
st.caption("Versioned file registry, independent of any ingestion run.")

with st.expander("\u2795 Upload a document"):
    with st.form("upload_doc"):
        name = st.text_input("Name")
        uploaded = st.file_uploader("File", accept_multiple_files=False)
        note = st.text_input("Note", value="")
        submitted = st.form_submit_button("Upload")
    if submitted:
        try:
            if uploaded is None:
                raise DocumentError("Choose a file first.")
            dto = UploadDocumentCommand().execute(name or uploaded.name, uploaded.name,
                                                  uploaded.getvalue(), note=note)
            st.success(f"Uploaded '{dto.name}' (id={dto.id}).")
            st.rerun()
        except DocumentError as e:
            st.error(str(e))

include_deleted = st.checkbox("Include deleted", value=False)
docs = ListDocumentsQuery().execute(include_deleted=include_deleted)
if not docs:
    st.info("No documents yet — upload one above.")
    st.stop()

for d in docs:
    with st.expander(f"{d.name} — v{d.current_version} ({d.status})"):
        st.caption(f"id: `{d.id}`  ·  filename: `{d.filename}`  ·  size: {d.size_bytes} bytes")
        for v in d.versions:
            st.markdown(f"- v{v.number}: `{v.filename}` ({v.size_bytes} bytes) — {v.note or 'no note'}")
        col1, col2 = st.columns(2)
        new_version = col1.file_uploader("Add new version", key=f"newver_{d.id}")
        if new_version is not None and col1.button("Upload version", key=f"upver_{d.id}"):
            try:
                CreateVersionCommand().execute(d.id, new_version.getvalue(), new_version.name)
                st.rerun()
            except DocumentError as e:
                st.error(str(e))
        if d.status == "active" and col2.button("Delete", key=f"del_{d.id}"):
            DeleteDocumentCommand().execute(d.id)
            st.rerun()
