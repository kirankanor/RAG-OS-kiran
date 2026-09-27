import sys
from pathlib import Path
import pandas as pd
import streamlit as st
sys.path.append(str(Path(__file__).resolve().parents[1]))
from lib import run_label
from modules.evaluation.infrastructure.manual_review.manual_review import run_score_summary
from modules.experiments.infrastructure.pipeline_orchestration.run_manager import delete_run
from shared.infrastructure.database.db_models import list_runs

st.set_page_config(page_title="Reports - RAG-OS", page_icon="\U0001F4CA", layout="wide")
st.title("\U0001F4CA Reports - Compare Runs")

runs = list_runs()
if not runs:
    st.warning("No runs yet. Create one on the **Upload Documents** page first.")
    st.stop()

rows = []
for run in runs:
    summary = run_score_summary(run.id)
    total = summary["total"]
    approval = f"{(summary['thumbs_up'] / total * 100):.0f}%" if total else "-"
    rows.append({"Run": run.name or run.id, "Parser": run.parser_name, "Chunker": run.chunker_name,
                 "Embedder": run.embedder_name, "Retriever": run.retriever_name,
                 "up": summary["thumbs_up"], "down": summary["thumbs_down"], "Approval": approval,
                 "Created": run.created_at, "_run_id": run.id})

df = pd.DataFrame(rows)
st.dataframe(df.drop(columns=["_run_id"]), use_container_width=True, hide_index=True)
st.caption("Ratings come from the Retrieval page. Wire evaluation.metrics.evaluate_run in for automatic metrics.")
st.divider()
st.subheader("Compare two runs side by side")
labels = {run_label(r): r for r in runs}
col1, col2 = st.columns(2)
left_label = col1.selectbox("Run A", options=list(labels.keys()), key="cmp_a")
right_label = col2.selectbox("Run B", options=list(labels.keys()), index=min(1, len(labels) - 1), key="cmp_b")
if left_label and right_label:
    run_a, run_b = labels[left_label], labels[right_label]
    compare_df = pd.DataFrame({
        "Run A": [run_a.parser_name, run_a.chunker_name, run_a.embedder_name, run_a.retriever_name],
        "Run B": [run_b.parser_name, run_b.chunker_name, run_b.embedder_name, run_b.retriever_name],
    }, index=["Parser", "Chunker", "Embedder", "Retriever"])
    st.table(compare_df)
st.divider()
st.subheader("Delete a run")
run_to_delete = st.selectbox("Run", options=list(labels.keys()), key="delete_run")
if st.button("\U0001F5D1\ufe0f Delete this run permanently", type="secondary"):
    delete_run(labels[run_to_delete].id)
    st.success("Deleted. Refresh the page.")
