import sys
from pathlib import Path
import streamlit as st
sys.path.append(str(Path(__file__).resolve().parents[1]))

from modules.strategies.application.commands.create_strategy import CreateStrategyCommand
from modules.strategies.application.queries.list_strategies import ListStrategiesQuery
from modules.strategies.application.queries.get_strategy import GetStrategyQuery
from modules.strategies.application.services.strategy_service import StrategyService
from modules.strategies.domain.exceptions import InvalidStrategyError
from modules.strategies.domain.models.chunker_config import ChunkerConfig
from modules.strategies.domain.models.embedding_config import EmbeddingConfig
from modules.strategies.domain.models.parser_config import ParserConfig
from modules.strategies.domain.models.reranker_config import RerankerConfig
from modules.strategies.domain.models.retrieval_config import RetrievalConfig
from modules.strategies.infrastructure.registry.chunker_registry import chunker_registry
from modules.strategies.infrastructure.registry.embedding_registry import embedder_registry
from modules.strategies.infrastructure.registry.parser_registry import parser_registry
from modules.strategies.infrastructure.registry.reranker_registry import reranker_registry
from modules.strategies.infrastructure.registry.retriever_registry import retriever_registry

st.set_page_config(page_title="Strategies - RAG-OS", page_icon="\U0001F9E9", layout="wide")
st.title("\U0001F9E9 Strategies")
st.caption("Saved, versioned parser+chunker+embedder+retrieval(+reranker) configs.")

with st.expander("\u2795 Create a new strategy"):
    with st.form("create_strategy"):
        name = st.text_input("Name")
        description = st.text_area("Description", value="")
        col1, col2, col3 = st.columns(3)
        chunker_name = col1.selectbox("Chunker", chunker_registry.names())
        embedder_name = col2.selectbox("Embedder", embedder_registry.names())
        retriever_name = col3.selectbox("Retriever", retriever_registry.names())
        top_k = st.number_input("top_k", min_value=1, value=5)
        use_reranker = st.checkbox("Add a reranker")
        reranker_name = st.selectbox("Reranker", reranker_registry.names()) if use_reranker else ""
        submitted = st.form_submit_button("Create")
    if submitted:
        try:
            CreateStrategyCommand().execute(
                name=name, chunker=ChunkerConfig(chunker_name), embedder=EmbeddingConfig(embedder_name),
                retrieval=RetrievalConfig(retriever_name, top_k=int(top_k)), parser=ParserConfig(),
                reranker=RerankerConfig(reranker_name) if reranker_name else None, description=description)
            st.success(f"Created strategy '{name}'.")
            st.rerun()
        except InvalidStrategyError as e:
            st.error("; ".join(e.errors) or str(e))

include_archived = st.checkbox("Include archived", value=False)
strategies = ListStrategiesQuery().execute(include_archived=include_archived)
if not strategies:
    st.info("No strategies yet — create one above.")
    st.stop()

for s in strategies:
    label = f"{s.name} v{s.version.number}" + (" (archived)" if s.is_archived else "")
    with st.expander(label):
        st.write(s.description or "_no description_")
        st.json({"parser": s.parser.to_dict(), "chunker": s.chunker.to_dict(),
                 "embedder": s.embedder.to_dict(), "retrieval": s.retrieval.to_dict(),
                 "reranker": s.reranker.to_dict() if s.reranker else None})
        versions = StrategyService().repository.list_versions(str(s.id))
        st.caption(f"Versions: {versions}  ·  id: `{s.id}`")
        if not s.is_archived and st.button("Archive", key=f"archive_{s.id}"):
            StrategyService().archive(str(s.id))
            st.rerun()
