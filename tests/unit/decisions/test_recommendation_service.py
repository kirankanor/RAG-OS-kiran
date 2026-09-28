import pytest

from modules.corpus_analysis.application.services.corpus_analysis_service import CorpusAnalysisService
from modules.decisions.application.services.recommendation_service import RecommendationService
from modules.decisions.domain.exceptions import DecisionNotFoundError, InvalidDecisionError
from modules.evaluation.domain.entities.evaluation_run import EvaluationRun, EvaluationStatus
from modules.evaluation.domain.models.evaluation_result import EvaluationResult
from modules.evaluation.domain.models.metric_result import MetricResult
from modules.experiments.domain.entities.experiment_run import ExperimentRun
from modules.experiments.domain.value_objects.experiment_status import ExperimentStatus
from modules.strategies.domain.entities.strategy import Strategy
from modules.strategies.domain.models.chunker_config import ChunkerConfig
from modules.strategies.domain.models.embedding_config import EmbeddingConfig
from modules.strategies.domain.models.retrieval_config import RetrievalConfig
from shared.ai.llm import Generator, generator_registry
from shared.domain.types import Document


class _FakeGen(Generator):
    name = "test_fake_gen"

    def generate(self, query, results):
        return "fake explanation"


try:
    generator_registry.register("test_fake_gen", "test double")(_FakeGen)
except ValueError:
    pass  # already registered


def _strategy(name, embedder="local_minilm"):
    return Strategy(name=name, chunker=ChunkerConfig("recursive_char"), embedder=EmbeddingConfig(embedder),
                    retrieval=RetrievalConfig("faiss_flat_l2"))


def _metrics(x):
    return EvaluationResult(k=3, num_queries=1, metrics=[
        MetricResult("recall@3", x), MetricResult("mrr", x), MetricResult("ndcg@3", x)])


class _World:
    """Fake collaborators standing in for the experiments/evaluation/strategies/corpus services."""

    def __init__(self, status=EvaluationStatus.COMPLETED):
        self.fast, self.slow = _strategy("fast"), _strategy("slow")
        self.runs = [
            ExperimentRun(id="r1", experiment_id="e1", strategy_id=str(self.fast.id),
                          status=ExperimentStatus.COMPLETED, duration_seconds=1.0),
            ExperimentRun(id="r2", experiment_id="e1", strategy_id=str(self.slow.id),
                          status=ExperimentStatus.COMPLETED, duration_seconds=4.0)]
        self.evals = [
            EvaluationRun(dataset_id="d1", experiment_id="e1", experiment_run_id="r1",
                          strategy_id=str(self.fast.id), status=status, result=_metrics(0.7)),
            EvaluationRun(dataset_id="d1", experiment_id="e1", experiment_run_id="r2",
                          strategy_id=str(self.slow.id), status=status, result=_metrics(0.8))]
        self.profile = CorpusAnalysisService().analyze_documents(
            [Document(source_filename="a.txt", text="the cat and the dog sat on the mat with the bone. " * 5)],
            analyzers=["size", "language"])

    def get(self, experiment_id):          # experiments.get
        assert experiment_id == "e1"
        return type("Exp", (), {"runs": self.runs})()

    def compare(self, dataset_id, experiment_id):  # evaluation.compare
        return self.evals

    def strategy_get(self, strategy_id, version=None):
        return {str(self.fast.id): self.fast, str(self.slow.id): self.slow}[strategy_id]

    def get_profile(self, profile_id):     # corpus.get_profile
        assert profile_id == "p1"
        return self.profile


def _service(world):
    return RecommendationService(
        experiments=type("E", (), {"get": staticmethod(world.get)})(),
        evaluation=type("V", (), {"compare": staticmethod(world.compare)})(),
        strategies=type("S", (), {"get": staticmethod(world.strategy_get)})(),
        corpus=type("C", (), {"get_profile": staticmethod(world.get_profile)})())


def test_make_decision_uses_measured_latency_and_persists(isolated_env):
    world = _World()
    svc = _service(world)
    d = svc.make_decision("e1", "d1")
    assert d.winner.strategy_name == "fast"          # 0.1 less quality, but 4x faster
    assert d.winner.factor("latency").unit == "s" and d.winner.factor("corpus_fit") is None
    assert d.corpus_profile_id == "" and d.tradeoffs and d.explanation.startswith("Recommended: fast")
    assert svc.get(d.id).to_dict() == d.to_dict()
    assert [x.id for x in svc.list("e1")] == [d.id] and svc.list("other") == []


def test_corpus_profile_adds_fit_factor(isolated_env):
    d = _service(_World()).make_decision("e1", "d1", corpus_profile_id="p1")
    assert d.corpus_profile_id == "p1" and d.winner.factor("corpus_fit") is not None
    assert "corpus_fit" in d.weights


def test_weights_constraints_and_llm_explainer(isolated_env):
    svc = _service(_World())
    d = svc.make_decision("e1", "d1", weights={"quality": 1},
                          constraints=[{"metric": "latency", "operator": "<=", "value": 2}],
                          explain_with="test_fake_gen")
    assert d.winner.strategy_name == "fast" and d.explanation == "fake explanation"
    assert d.recommendations[1].eligible is False


def test_errors(isolated_env):
    svc = _service(_World())
    with pytest.raises(InvalidDecisionError):
        svc.make_decision("e1", "d1", constraints=[{"metric": "speed", "operator": "<=", "value": 1}])
    with pytest.raises(InvalidDecisionError):
        svc.make_decision("e1", "d1", constraints=[{"metric": "cost"}])
    with pytest.raises(InvalidDecisionError):
        svc.make_decision("e1", "d1", explain_with="nope")
    with pytest.raises(InvalidDecisionError):
        _service(_World(status=EvaluationStatus.FAILED)).make_decision("e1", "d1")
    with pytest.raises(DecisionNotFoundError):
        svc.get("nope")
