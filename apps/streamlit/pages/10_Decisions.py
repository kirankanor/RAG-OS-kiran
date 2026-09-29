import sys
from pathlib import Path
import streamlit as st
sys.path.append(str(Path(__file__).resolve().parents[1]))

from modules.corpus_analysis.application.queries.get_corpus_profile import GetCorpusProfileQuery
from modules.decisions.application.commands.make_decision import MakeDecisionCommand
from modules.decisions.application.queries.get_decision import GetDecisionQuery
from modules.decisions.domain.exceptions import InvalidDecisionError
from modules.evaluation.application.services.evaluation_service import EvaluationService
from modules.experiments.application.services.experiment_service import ExperimentService
from shared.ai.llm import generator_registry

st.set_page_config(page_title="Decisions - RAG-OS", page_icon="\u2696\ufe0f", layout="wide")
st.title("\u2696\ufe0f Decisions")
st.caption("Recommend a strategy from an evaluated experiment.")

experiments = ExperimentService().list()
datasets = EvaluationService().list_datasets()
profiles = GetCorpusProfileQuery().list()
if not experiments or not datasets:
    st.info("Need at least one experiment and one dataset (see the Experiments / Evaluation pages).")
    st.stop()

exp_label = {f"{e.name} ({e.status.value})": str(e.id) for e in experiments}
ds_label = {f"{d.name} ({d.id})": d.id for d in datasets}
profile_label = {"(none)": "", **{f"profile {p.id}": p.id for p in profiles}}

with st.form("make_decision"):
    experiment_id = exp_label[st.selectbox("Experiment", options=list(exp_label))]
    dataset_id = ds_label[st.selectbox("Dataset", options=list(ds_label))]
    corpus_profile_id = profile_label[st.selectbox("Corpus profile (optional)", options=list(profile_label))]
    col1, col2, col3 = st.columns(3)
    w_quality = col1.slider("Weight: quality", 0.0, 1.0, 0.6)
    w_latency = col2.slider("Weight: latency", 0.0, 1.0, 0.15)
    w_cost = col3.slider("Weight: cost", 0.0, 1.0, 0.15)
    names = [""] + generator_registry.names()
    explain_with = st.selectbox("Explain with (optional LLM)", names)
    submitted = st.form_submit_button("Make decision")

if submitted:
    try:
        weights = {"quality": w_quality, "latency": w_latency, "cost": w_cost}
        if corpus_profile_id:
            weights["corpus_fit"] = 0.10
        decision = MakeDecisionCommand().execute(experiment_id, dataset_id, corpus_profile_id,
                                                 weights=weights, explain_with=explain_with)
        st.success(f"Decision made: winner = {decision.winner.strategy_name if decision.winner else 'none'}")
    except InvalidDecisionError as e:
        st.error("; ".join(e.errors) or str(e))

st.divider()
st.subheader("Past decisions for this experiment")
for d in GetDecisionQuery().for_experiment(experiment_id):
    with st.expander(f"Decision {d.id} — {d.created_at}"):
        for r in d.recommendations:
            st.markdown(f"**#{r.rank} {r.strategy_name}** v{r.strategy_version} — "
                        f"score {r.total_score:.2f}" + ("" if r.eligible else " (ineligible)"))
            st.caption(", ".join(f"{f.name}={f.display}" for f in r.factors))
        if d.tradeoffs:
            st.markdown("**Trade-offs:** " + " ".join(t.statement for t in d.tradeoffs))
        if d.explanation:
            st.markdown(f"**Explanation:** {d.explanation}")
