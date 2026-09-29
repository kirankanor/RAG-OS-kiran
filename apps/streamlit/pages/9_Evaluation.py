import sys
from pathlib import Path
import streamlit as st
sys.path.append(str(Path(__file__).resolve().parents[1]))

from modules.evaluation.application.commands.compare_results import CompareResultsCommand
from modules.evaluation.application.commands.create_dataset import CreateDatasetCommand
from modules.evaluation.application.commands.run_evaluation import RunEvaluationCommand
from modules.evaluation.application.services.evaluation_service import EvaluationService
from modules.evaluation.domain.exceptions import EvaluationError, InvalidDatasetError
from modules.experiments.application.services.experiment_service import ExperimentService

st.set_page_config(page_title="Evaluation - RAG-OS", page_icon="\U0001F4CF", layout="wide")
st.title("\U0001F4CF Evaluation")
st.caption("Score a finished experiment's runs against a query/relevant-text dataset.")

with st.expander("\u2795 Create a dataset"):
    with st.form("create_dataset"):
        ds_name = st.text_input("Dataset name")
        rows_raw = st.text_area("Queries — one per line as `query | relevant text`", value="")
        submitted = st.form_submit_button("Create")
    if submitted:
        try:
            queries = []
            for line in rows_raw.splitlines():
                if "|" not in line:
                    continue
                q, t = line.split("|", 1)
                queries.append({"query": q.strip(), "relevant_texts": [t.strip()]})
            CreateDatasetCommand().execute(ds_name, queries)
            st.success(f"Created dataset '{ds_name}'.")
            st.rerun()
        except InvalidDatasetError as e:
            st.error("; ".join(e.errors) or str(e))

datasets = EvaluationService().list_datasets()
experiments = ExperimentService().list()
if not datasets or not experiments:
    st.info("Need at least one dataset and one experiment to evaluate.")
    st.stop()

ds_label = {f"{d.name} ({d.id})": d.id for d in datasets}
exp_label = {f"{e.name} ({e.status.value})": str(e.id) for e in experiments}
col1, col2 = st.columns(2)
dataset_id = ds_label[col1.selectbox("Dataset", options=list(ds_label))]
experiment_id = exp_label[col2.selectbox("Experiment", options=list(exp_label))]

if st.button("\u25b6\ufe0f Run evaluation"):
    try:
        runs = RunEvaluationCommand().execute(dataset_id, experiment_id)
        st.success(f"Evaluated {len(runs)} run(s).")
    except EvaluationError as e:
        st.error(str(e))

sort_by = st.selectbox("Sort by", ["mrr", "recall", "precision", "ndcg"])
ranked = CompareResultsCommand().execute(dataset_id, experiment_id, sort_by)
if not ranked:
    st.info("No evaluation runs yet for this dataset/experiment.")
else:
    for r in ranked:
        status = "\u2705" if r.status.value == "completed" else "\u274c"
        st.markdown(f"{status} strategy `{r.strategy_id}` v{r.strategy_version} — "
                    + (", ".join(f"{k}={v:.3f}" for k, v in r.result.summary().items())
                       if r.status.value == "completed" else r.error_message))
