import sys
from pathlib import Path
import streamlit as st
sys.path.append(str(Path(__file__).resolve().parents[1]))

from modules.artifacts.application.commands.generate_code import GenerateCodeCommand
from modules.artifacts.application.commands.generate_report import GenerateReportCommand
from modules.artifacts.application.commands.package_project import PackageProjectCommand
from modules.artifacts.application.queries.list_artifacts import ListArtifactsQuery
from modules.artifacts.domain.exceptions import ArtifactError
from modules.decisions.application.queries.get_decision import GetDecisionQuery
from modules.projects.application.queries.list_projects import ListProjectsQuery
from modules.strategies.application.queries.list_strategies import ListStrategiesQuery

st.set_page_config(page_title="Artifacts - RAG-OS", page_icon="\U0001F4E6", layout="wide")
st.title("\U0001F4E6 Artifacts")
st.caption("Generated reports, code and project packages.")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Decision report")
    decisions = GetDecisionQuery().list()
    if decisions:
        d_id = st.selectbox("Decision", options=[d.id for d in decisions],
                            format_func=lambda i: f"{i} ({[d for d in decisions if d.id == i][0].created_at})")
        if st.button("Generate report"):
            try:
                GenerateReportCommand().execute(d_id)
                st.rerun()
            except ArtifactError as e:
                st.error(str(e))
    else:
        st.caption("No decisions yet.")

with col2:
    st.subheader("Strategy code")
    strategies = ListStrategiesQuery().execute()
    if strategies:
        s_id = st.selectbox("Strategy", options=[str(s.id) for s in strategies],
                            format_func=lambda i: next(f"{s.name} v{s.version.number}"
                                                        for s in strategies if str(s.id) == i))
        if st.button("Generate script"):
            try:
                GenerateCodeCommand().execute(s_id)
                st.rerun()
            except ArtifactError as e:
                st.error(str(e))
    else:
        st.caption("No strategies yet.")

with col3:
    st.subheader("Project package")
    projects = ListProjectsQuery().execute()
    if projects:
        p_id = st.selectbox("Project", options=[p.id for p in projects],
                            format_func=lambda i: next(p.name for p in projects if p.id == i))
        include_docs = st.checkbox("Include document files")
        if st.button("Package project"):
            try:
                PackageProjectCommand().execute(p_id, include_documents=include_docs)
                st.rerun()
            except ArtifactError as e:
                st.error(str(e))
    else:
        st.caption("No projects yet.")

st.divider()
artifacts = ListArtifactsQuery().execute()
if not artifacts:
    st.info("No artifacts generated yet.")
    st.stop()

for a in artifacts:
    with st.expander(f"[{a.type.value}] {a.name} — {a.status.value}"):
        st.caption(f"id: `{a.id}`  ·  source: {a.source_type}/{a.source_id}  ·  "
                   f"{a.size_bytes} bytes  ·  {a.created_at}")
        if a.status.value == "completed":
            try:
                data = ListArtifactsQuery().service.read_bytes(a.id)
                st.download_button("Download", data=data, file_name=a.filename, key=f"dl_{a.id}")
            except ArtifactError as e:
                st.error(str(e))
        else:
            st.error(a.error_message)
