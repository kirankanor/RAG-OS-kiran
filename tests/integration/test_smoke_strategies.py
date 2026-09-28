import pytest

from modules.strategies.application.commands.create_strategy import CreateStrategyCommand
from modules.strategies.application.commands.generate_strategies import GenerateStrategiesCommand
from modules.strategies.application.queries.get_strategy import GetStrategyQuery
from modules.strategies.application.queries.list_strategies import ListStrategiesQuery
from modules.strategies.application.services.strategy_service import StrategyService
from modules.strategies.domain.exceptions import InvalidStrategyError, StrategyNotFoundError
from modules.strategies.domain.models.chunker_config import ChunkerConfig
from modules.strategies.domain.models.embedding_config import EmbeddingConfig
from modules.strategies.domain.models.reranker_config import RerankerConfig
from modules.strategies.domain.models.retrieval_config import RetrievalConfig


def _create(name="s1", chunker="fixed_size"):
    return CreateStrategyCommand().execute(
        name, ChunkerConfig(chunker, {"chunk_size": 500, "overlap": 50}),
        EmbeddingConfig("local_minilm"), RetrievalConfig("faiss_flat_l2", top_k=7))


def test_create_get_list(isolated_env):
    s = _create()
    got = GetStrategyQuery().execute(str(s.id))
    assert got.name == "s1" and got.version.number == 1 and got.retrieval.top_k == 7
    assert got.reranker is None
    assert [x.id for x in ListStrategiesQuery().execute()] == [s.id]


def test_revise_bumps_version_and_keeps_history(isolated_env):
    s = _create()
    svc = StrategyService()
    revised = svc.revise(str(s.id), reranker=RerankerConfig("cross_encoder"))
    assert revised.version.number == 2
    assert svc.revise(str(s.id), reranker=RerankerConfig("cross_encoder")).version.number == 2  # no-op
    old = GetStrategyQuery().execute(str(s.id), version=1)
    assert old.reranker is None
    assert svc.repository.list_versions(str(s.id)) == [1, 2]
    assert svc.get(str(s.id)).reranker.name == "cross_encoder"


def test_invalid_and_missing(isolated_env):
    with pytest.raises(InvalidStrategyError):
        _create(chunker="does_not_exist")
    with pytest.raises(StrategyNotFoundError):
        GetStrategyQuery().execute("nope")
    with pytest.raises(StrategyNotFoundError):
        GetStrategyQuery().execute(str(_create().id), version=9)


def test_archive_hides_from_list(isolated_env):
    s = _create()
    StrategyService().archive(str(s.id))
    assert ListStrategiesQuery().execute() == []
    assert len(ListStrategiesQuery().execute(include_archived=True)) == 1


def test_to_run_config(isolated_env):
    rc = _create().to_run_config()
    assert rc.chunker_name == "fixed_size" and rc.chunker_params["chunk_size"] == 500
    assert rc.embedder_name == "local_minilm" and rc.reranker_name == ""


def test_generate_presets_persist(isolated_env):
    candidates = GenerateStrategiesCommand().execute(count=3, persist=True)
    assert len(candidates) == 3
    assert len(ListStrategiesQuery().execute()) == 3