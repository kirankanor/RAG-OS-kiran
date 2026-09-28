from modules.corpus_analysis.application.commands.analyze_corpus import AnalyzeCorpusCommand
from modules.decisions.application.commands.make_decision import MakeDecisionCommand
from modules.decisions.application.queries.get_decision import GetDecisionQuery
from modules.evaluation.application.commands.run_evaluation import RunEvaluationCommand
from modules.experiments.application.services.experiment_orchestrator import ExperimentOrchestrator
from modules.experiments.application.services.experiment_service import ExperimentService
# Importing these also registers the test_hash embedder / test_bruteforce retriever.
from tests.integration.test_smoke_evaluation import _dataset
from tests.integration.test_smoke_experiments import _config, _strategy


def _evaluated_experiment(env):
    a, b = _strategy("a", chunk_size=100), _strategy("b", chunk_size=60)
    svc = ExperimentService()
    exp = svc.create("cmp", _config(env), [str(a.id), str(b.id)])
    ExperimentOrchestrator(svc).run(str(exp.id))
    ds = _dataset()
    RunEvaluationCommand().execute(ds.id, str(exp.id))
    return exp, ds


def test_decision_end_to_end(isolated_env):
    exp, ds = _evaluated_experiment(isolated_env)
    profile = AnalyzeCorpusCommand().execute(exp.config.file_paths)
    d = MakeDecisionCommand().execute(str(exp.id), ds.id, corpus_profile_id=profile.id)

    assert d.winner is not None and [r.rank for r in d.recommendations] == [1, 2]
    assert [f.name for f in d.winner.factors] == ["quality", "latency", "cost", "corpus_fit"]
    assert d.winner.factor("latency").unit == "s"
    assert abs(sum(d.weights.values()) - 1.0) < 1e-9
    assert d.winner.strategy_name in d.explanation

    q = GetDecisionQuery()
    assert q.execute(d.id).to_dict() == d.to_dict()
    assert [x.id for x in q.for_experiment(str(exp.id))] == [d.id]


def test_decision_with_impossible_constraint_has_no_winner(isolated_env):
    exp, ds = _evaluated_experiment(isolated_env)
    d = MakeDecisionCommand().execute(str(exp.id), ds.id,
                                      constraints=[{"metric": "quality", "operator": ">=", "value": 2.0}])
    assert d.winner is None and "No strategy satisfied all constraints" in d.explanation
