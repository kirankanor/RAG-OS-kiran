import math

import pytest

from modules.evaluation.application.commands.compare_results import CompareResultsCommand
from modules.evaluation.application.commands.create_dataset import CreateDatasetCommand
from modules.evaluation.application.commands.run_evaluation import RunEvaluationCommand
from modules.evaluation.application.queries.get_evaluation import GetEvaluationQuery
from modules.evaluation.application.services.metric_service import match_snippets
from modules.evaluation.domain.entities.evaluation_run import EvaluationStatus
from modules.evaluation.domain.exceptions import (
    DatasetNotFoundError, EvaluationStateError, InvalidDatasetError,
)
from modules.evaluation.infrastructure.metrics.mrr import reciprocal_rank
from modules.evaluation.infrastructure.metrics.ndcg import ndcg_at_k
from modules.evaluation.infrastructure.metrics.precision import precision_at_k
from modules.evaluation.infrastructure.metrics.recall import recall_at_k
from modules.experiments.application.services.experiment_orchestrator import ExperimentOrchestrator
from modules.experiments.application.services.experiment_service import ExperimentService
# Importing this module also registers the test_hash embedder / test_bruteforce retriever.
from tests.integration.test_smoke_experiments import _config, _strategy


def test_metric_math():
    hits = [frozenset({0}), frozenset(), frozenset({1})]
    assert recall_at_k(hits, 2, 3) == 1.0
    assert recall_at_k(hits, 2, 1) == 0.5
    assert precision_at_k(hits, 3) == pytest.approx(2 / 3)
    assert reciprocal_rank(hits) == 1.0
    assert reciprocal_rank([frozenset(), frozenset({0})]) == 0.5
    assert reciprocal_rank([frozenset()]) == 0.0
    assert ndcg_at_k(hits, 2, 3) == pytest.approx(1.5 / (1 + 1 / math.log2(3)))
    assert recall_at_k([], 2, 3) == 0.0 and precision_at_k([], 3) == 0.0


def test_snippet_matching_ignores_case_and_whitespace():
    assert match_snippets("The  Cats\npurr loudly", ["cats purr", "dogs"]) == frozenset({0})


def test_dataset_validation(isolated_env):
    with pytest.raises(InvalidDatasetError):
        CreateDatasetCommand().execute("", [])
    with pytest.raises(InvalidDatasetError):
        CreateDatasetCommand().execute("d", [{"query": "q", "relevant_texts": [" "]}])
    with pytest.raises(InvalidDatasetError):
        CreateDatasetCommand().execute("d", [{"query": "q", "relevant_texts": ["a"]},
                                             {"query": "q", "relevant_texts": ["b"]}])


def _dataset():
    return CreateDatasetCommand().execute("d1", [
        {"query": "how do cats sleep", "relevant_texts": ["Cats purr"]},
        {"query": "not in the experiment", "relevant_texts": ["whatever"]},
    ])


def test_evaluate_and_compare(isolated_env):
    a, b = _strategy("a", chunk_size=100), _strategy("b", chunk_size=60)
    svc = ExperimentService()
    exp = svc.create("cmp", _config(isolated_env), [str(a.id), str(b.id)])
    ds = _dataset()

    with pytest.raises(EvaluationStateError):  # still pending
        RunEvaluationCommand().execute(ds.id, str(exp.id))

    ExperimentOrchestrator(svc).run(str(exp.id))
    runs = RunEvaluationCommand().execute(ds.id, str(exp.id))
    assert len(runs) == 2
    for r in runs:
        assert r.status == EvaluationStatus.COMPLETED
        assert r.result.num_queries == 1          # second dataset query not in results
        s = r.result.summary()
        assert set(s) == {"recall@3", "precision@3", "mrr", "ndcg@3"}
        assert all(0.0 <= v <= 1.0 for v in s.values())
        assert s["mrr"] > 0

    got = GetEvaluationQuery().execute(runs[0].id)
    assert got.result.summary() == runs[0].result.summary()
    assert got.result.metrics[0].per_query.keys() == {"how do cats sleep"}

    ranked = CompareResultsCommand().execute(ds.id, str(exp.id), sort_by="mrr")
    assert len(ranked) == 2
    assert ranked[0].result.get("mrr") >= ranked[1].result.get("mrr")

    RunEvaluationCommand().execute(ds.id, str(exp.id), k=2)   # re-evaluate with other k
    assert len(GetEvaluationQuery().for_experiment(str(exp.id))) == 4
    assert len(CompareResultsCommand().execute(ds.id, str(exp.id), sort_by="recall")) == 2

    with pytest.raises(DatasetNotFoundError):
        CompareResultsCommand().execute("nope", str(exp.id))


def test_ingestion_experiment_records_failed_evaluation(isolated_env):
    s = _strategy("s")
    svc = ExperimentService()
    exp = svc.create("ing", _config(isolated_env, runner="ingestion", queries=[]), [str(s.id)])
    ExperimentOrchestrator(svc).run(str(exp.id))
    [run] = RunEvaluationCommand().execute(_dataset().id, str(exp.id))
    assert run.status == EvaluationStatus.FAILED and "no retrieval results" in run.error_message
