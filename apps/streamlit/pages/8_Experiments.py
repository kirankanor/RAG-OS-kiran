import sys
from pathlib import Path
import streamlit as st
sys.path.append(str(Path(__file__).resolve().parents[1]))

from modules.experiments.application.commands.create_experiment import CreateExperimentCommand
from modules.experiments.application.commands.run_experiment import RunExperimentCommand
from modules.experiments.application.commands.stop_experiment import StopExperimentCommand
from modules.experiments.application.services.experiment_service import ExperimentService
from modules.experiments.domain.exceptions import InvalidExperimentError, ExperimentStateError
from modules.experiments.domain.models.experiment_config import ExperimentConfig
from modules.strategies.application.queries.list_strategies import ListStrategiesQuery
from shared.ai.llm import generator_registry
from shared.infrastructure.storage.local_file_store import save_upload

st.set_page_config(page_title="Experiments - RAG-OS", page_icon="\U0001F9EA", layout="wide")
st.title("\U0001F9EA Experiments")
st.caption("Run one or more saved strategies over the same files and queries.")

strategies = ListStrategiesQuery().execute()
if not strategies:
    st.warning("No strategies yet — create one on the **Strategies** page first.")
    st.stop()

with st.expander("\u2795 Create a new experiment"):
    with st.form("create_experiment"):
        name = st.text_input("Name")
        runner = st.selectbox("Runner", ["retrieval", "ingestion", "rag"])
        picked = st.multiselect("Strategies", options=[str(s.id) for s in strategies],
                                format_func=lambda i: next(f"{s.name} v{s.version.number}"
                                                            for s in strategies if str(s.id) == i))
        uploaded = st.file_uploader("Files", accept_multiple_files=True)
        queries_raw = st.text_area("Queries (one per line)", value="")
        generator_name = ""
        if runner == "rag":
            names = generator_registry.names()
            generator_name = st.selectbox("Generator", names) if names else st.error("No generators registered.")
        submitted = st.form_submit_button("Create")
    if submitted:
        try:
            if not uploaded:
                raise InvalidExperimentError("At least one file is required.", ["No files uploaded."])
            paths = [str(save_upload(f.getvalue(), f.name, "experiments-tmp")) for f in uploaded]
            queries = [q.strip() for q in queries_raw.splitlines() if q.strip()]
            config = ExperimentConfig(runner=runner, file_paths=paths, queries=queries,
                                      generator_name=generator_name)
            exp = CreateExperimentCommand().execute(name, config, picked)
            st.success(f"Created experiment '{exp.name}' (id={exp.id}).")
            st.rerun()
        except InvalidExperimentError as e:
            st.error("; ".join(e.errors) or str(e))

experiments = ExperimentService().list()
if not experiments:
    st.info("No experiments yet — create one above.")
    st.stop()

for exp in experiments:
    with st.expander(f"{exp.name} — {exp.status.value}"):
        st.caption(f"id: `{exp.id}`  ·  runner: `{exp.config.runner}`  ·  queries: {exp.config.queries}")
        col1, col2 = st.columns(2)
        if exp.status.value == "pending" and col1.button("\u25b6\ufe0f Run", key=f"run_{exp.id}"):
            try:
                RunExperimentCommand().execute(str(exp.id))
                st.rerun()
            except ExperimentStateError as e:
                st.error(str(e))
        if exp.status.value in ("pending", "running") and col2.button("\u23f9 Stop", key=f"stop_{exp.id}"):
            StopExperimentCommand().execute(str(exp.id))
            st.rerun()
        for r in exp.runs:
            st.markdown(f"- strategy `{r.strategy_id}` v{r.strategy_version}: **{r.status.value}**"
                        + (f" — {r.error_message}" if r.error_message else ""))
            if r.result.get("queries"):
                st.json(r.result["queries"])
