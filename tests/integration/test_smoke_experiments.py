import zlib

import pytest

from modules.experiments.application.services.experiment_orchestrator import ExperimentOrchestrator
from modules.experiments.application.services.experiment_service import ExperimentService
from modules.experiments.domain.exceptions import (
    ExperimentStateError, InvalidExperimentError,
)
from modules.experiments.domain.models.experiment_config import ExperimentConfig
from modules.experiments.domain.value_objects.experiment_status import ExperimentStatus
from modules.experiments.infrastructure.execution.local_executor import LocalExecutor
from modules.strategies.application.services.strategy_service import StrategyService
from modules.strategies.domain.exceptions import StrategyNotFoundError
from modules.strategies.domain.models.chunker_config import ChunkerConfig
from modules.strategies.domain.models.embedding_config import EmbeddingConfig
from modules.strategies.domain.models.parser_config import ParserConfig
from modules.strategies.domain.models.retrieval_config import RetrievalConfig
from shared.ai.embeddings import Embedder, embedder_registry
from shared.domain.types import RetrievalResult
from shared.infrastructure.database.db_models import get_run
from shared.retrieval import Retriever, retriever_registry


class HashEmbedder(Embedder):
    name = "test_hash"
    dim = 16

    def embed(self, texts):
        out = []
        for t in texts:
            v = [0.0] * 16
            for w in t.lower().split():
                v[zlib.crc32(w.encode()) % 16] += 1.0
            out.append(v)
        return out


class BruteForceRetriever(Retriever):
    name = "test_bruteforce"

    def __init__(self):
        self._chunks, self._vectors = [], []

    def build(self, chunks, vectors):
        self._chunks, self._vectors = chunks, vectors

    @staticmethod
    def _cos(a, b):
        dot = sum(x * y for x, y in zip(a, b))
        na, nb = sum(x * x for x in a) ** 0.5, sum(y * y for y in b) ** 0.5
        return dot / (na * nb) if na and nb else 0.0

    def retrieve(self, query_vector, top_k=5, query_text=""):
        scored = sorted(((self._cos(query_vector, v), c) for v, c in zip(self._vectors, self._chunks)),
                        key=lambda x: x[0], reverse=True)[:top_k]
        return [RetrievalResult(chunk_id=c.id, score=float(s), rank=i, text=c.text, metadata=c.metadata)
                for i, (s, c) in enumerate(scored)]


for _reg, _name, _cls in ((embedder_registry, "test_hash", HashEmbedder),
                          (retriever_registry, "test_bruteforce", BruteForceRetriever)):
    try:
        _reg.register(_name, "test double")(_cls)
    except ValueError:
        pass  # already registered


def _strategy(name, chunker="fixed_size", chunk_size=100, top_k=3):
    params = {} if chunker == "contextual" else {"chunk_size": chunk_size, "overlap": 0}
    return StrategyService().create(
        name, ParserConfig(), ChunkerConfig(chunker, params), EmbeddingConfig("test_hash"),
        RetrievalConfig("test_bruteforce", top_k=top_k))


def _file(env):
    f = env / "doc.txt"
    f.write_text("Cats purr and sleep all day long. " * 6 + "Rockets burn fuel to reach orbit. " * 6,
                 encoding="utf-8")
    return str(f)


def _config(env, **kw):
    return ExperimentConfig(runner=kw.pop("runner", "retrieval"), file_paths=[_file(env)],
                            queries=kw.pop("queries", ["how do cats sleep"]), **kw)


def test_create_pins_version_and_validates(isolated_env):
    s = _strategy("s1")
    svc = ExperimentService()
    exp = svc.create("e1", _config(isolated_env), [str(s.id)])
    assert exp.strategy_refs[0].version == 1 and len(exp.runs) == 1

    StrategyService().revise(str(s.id), description="changed", name="s1-renamed")
    assert svc.get(str(exp.id)).strategy_refs[0].version == 1  # still pinned

    with pytest.raises(InvalidExperimentError):
        svc.create("bad", ExperimentConfig(runner="nope", file_paths=["missing.txt"]), [str(s.id)])
    with pytest.raises(InvalidExperimentError):
        svc.create("noq", _config(isolated_env, queries=[]), [str(s.id)])
    with pytest.raises(InvalidExperimentError):
        svc.create("norag", _config(isolated_env, runner="rag"), [str(s.id)])
    with pytest.raises(StrategyNotFoundError):
        svc.create("ghost", _config(isolated_env), ["does-not-exist"])


def test_run_two_strategies(isolated_env):
    a, b = _strategy("a", chunk_size=100), _strategy("b", chunk_size=60)
    svc = ExperimentService()
    exp = svc.create("cmp", _config(isolated_env), [str(a.id), str(b.id)])
    done = ExperimentOrchestrator(svc).run(str(exp.id))

    assert done.status == ExperimentStatus.COMPLETED
    assert [r.status for r in done.runs] == [ExperimentStatus.COMPLETED] * 2
    for r in done.runs:
        assert get_run(r.pipeline_run_id) is not None          # legacy RunRow exists
        assert len(r.result["queries"]["how do cats sleep"]) == 3  # strategy top_k used
        assert r.duration_seconds >= 0

    with pytest.raises(ExperimentStateError):
        ExperimentOrchestrator(svc).run(str(exp.id))


def test_config_top_k_overrides_strategy(isolated_env):
    s = _strategy("s", top_k=3)
    svc = ExperimentService()
    exp = svc.create("k", _config(isolated_env, top_k=2), [str(s.id)])
    done = ExperimentOrchestrator(svc).run(str(exp.id))
    assert len(done.runs[0].result["queries"]["how do cats sleep"]) == 2


def test_failed_run_does_not_stop_others(isolated_env):
    good, bad = _strategy("good"), _strategy("bad", chunker="contextual")  # needs llm_fn -> fails
    svc = ExperimentService()
    exp = svc.create("mixed", _config(isolated_env), [str(bad.id), str(good.id)])
    done = ExperimentOrchestrator(svc).run(str(exp.id))

    assert done.status == ExperimentStatus.FAILED
    assert done.runs[0].status == ExperimentStatus.FAILED and "llm_fn" in done.runs[0].error_message
    assert done.runs[1].status == ExperimentStatus.COMPLETED


def test_stop_pending(isolated_env):
    s = _strategy("s")
    svc = ExperimentService()
    exp = svc.create("stopme", _config(isolated_env), [str(s.id)])
    stopped = svc.stop(str(exp.id))
    assert stopped.status == ExperimentStatus.CANCELLED
    assert stopped.runs[0].status == ExperimentStatus.CANCELLED
    with pytest.raises(ExperimentStateError):
        ExperimentOrchestrator(svc).run(str(exp.id))


def test_stop_between_runs(isolated_env):
    a, b = _strategy("a"), _strategy("b", chunk_size=60)
    svc = ExperimentService()
    exp = svc.create("mid", _config(isolated_env), [str(a.id), str(b.id)])

    class StopAfterFirst(LocalExecutor):
        def execute(self, runner, config, strategy):
            result = super().execute(runner, config, strategy)
            svc.stop(str(exp.id))
            return result

    done = ExperimentOrchestrator(svc, StopAfterFirst()).run(str(exp.id))
    assert done.status == ExperimentStatus.CANCELLED
    assert [r.status for r in done.runs] == [ExperimentStatus.COMPLETED, ExperimentStatus.CANCELLED]