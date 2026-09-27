import sys
from pathlib import Path
import streamlit as st
sys.path.append(str(Path(__file__).resolve().parents[1]))
from lib import get_cached_retriever_and_reranker, run_picker
from shared.ai.embeddings import embedder_registry
from modules.evaluation.infrastructure.manual_review.manual_review import save_rating
from shared.infrastructure.database.db_models import loads

st.set_page_config(page_title="Retrieval - RAG-OS", page_icon="\U0001F50E", layout="wide")
st.title("\U0001F50E Retrieval Playground")
st.caption("Run a query against a saved run's retriever and rate the results.")

run = run_picker(key="retrieval_run")
if run:
    st.markdown(f"**Retriever used:** `{run.retriever_name}`  -  embedder: `{run.embedder_name}`"
                + (f"  -  reranker: `{run.reranker_name}`" if run.reranker_name else ""))
    top_k = st.slider("top_k", min_value=1, max_value=20, value=5)
    query = st.text_input("Query")
    if query:
        with st.spinner("Embedding query + retrieving..."):
            retriever, reranker = get_cached_retriever_and_reranker(run.id)
            embedder = embedder_registry.create(run.embedder_name, **loads(run.embedder_params))
            query_vector = embedder.embed_query(query)
            fetch_k = top_k * 3 if reranker else top_k
            results = retriever.retrieve(query_vector, top_k=fetch_k, query_text=query)
            if reranker:
                results = reranker.rerank(query, results, top_k=top_k)
        if not results:
            st.warning("No results returned.")
        else:
            for r in results:
                with st.container(border=True):
                    st.markdown(f"**Rank {r.rank + 1}**  -  score `{r.score:.4f}`  -  chunk `{r.chunk_id}`")
                    st.write(r.text)
            st.divider()
            st.subheader("Rate this query's results")
            col1, col2 = st.columns(2)
            note = st.text_input("Note (optional)", key="rating_note")
            if col1.button("\U0001F44D Good results", use_container_width=True):
                save_rating(run.id, query, thumbs_up=True, note=note)
                st.success("Saved.")
            if col2.button("\U0001F44E Bad results", use_container_width=True):
                save_rating(run.id, query, thumbs_up=False, note=note)
                st.success("Saved.")
