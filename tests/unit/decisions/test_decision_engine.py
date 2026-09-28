import pytest

from modules.decisions.application.services.decision_engine import CandidateInput, DecisionEngine
from modules.decisions.application.services.tradeoff_analyzer import TradeoffAnalyzer
from modules.decisions.domain.entities.decision import Decision
from modules.decisions.domain.exceptions import InvalidDecisionError
from modules.decisions.domain.models.constraint import Constraint
from modules.decisions.domain.rules.quality_rules import corpus_fit, corpus_warnings, quality_value
from modules.decisions.infrastructure.llm.decision_explainer import LlmExplainer, TemplateExplainer
from modules.strategies.domain.entities.strategy import Strategy
from modules.strategies.domain.models.chunker_config import ChunkerConfig
from modules.strategies.domain.models.embedding_config import EmbeddingConfig
from modules.strategies.domain.models.reranker_config import RerankerConfig
from modules.strategies.domain.models.retrieval_config import RetrievalConfig


def _s(name, chunker="recursive_char", embedder="local_minilm", retrieval="faiss_flat_l2", reranker=None):
    return Strategy(name=name, chunker=ChunkerConfig(chunker), embedder=EmbeddingConfig(embedder),
                    retrieval=RetrievalConfig(retrieval),
                    reranker=RerankerConfig(reranker) if reranker else None)


def _m(x):
    return {"recall@3": x, "mrr": x, "ndcg@3": x}


def _pair(latency=None):
    cloud = _s("cloud", embedder="openai_text_embedding_3_small", retrieval="qdrant", reranker="cohere_rerank")
    local = _s("local")
    return [CandidateInput(cloud, _m(0.9), latency[0] if latency else None),
            CandidateInput(local, _m(0.85), latency[1] if latency else None)]


def test_cheap_local_wins_with_default_weights():
    recs, weights = DecisionEngine().decide(_pair())
    assert [r.strategy_name for r in recs] == ["local", "cloud"] and [r.rank for r in recs] == [1, 2]
    assert recs[0].total_score == pytest.approx(0.9, abs=1e-3)
    assert sum(weights.values()) == pytest.approx(1.0) and "corpus_fit" not in weights
    assert recs[0].factor("latency").unit == "units" and recs[0].factor("corpus_fit") is None


def test_quality_only_weights_flip_the_winner_and_produce_tradeoffs():
    recs, _ = DecisionEngine().decide(_pair(), weights={"quality": 1, "latency": 0, "cost": 0})
    assert recs[0].strategy_name == "cloud"
    tradeoffs = TradeoffAnalyzer().analyze(recs)
    assert {t.factor for t in tradeoffs} == {"latency", "cost"}
    assert all(t.strategy_name == "local" for t in tradeoffs)


def test_measured_latency_used_when_every_run_has_it():
    recs, _ = DecisionEngine().decide(_pair(latency=(4.0, 1.0)))
    by_name = {r.strategy_name: r.factor("latency") for r in recs}
    assert by_name["local"].unit == "s" and by_name["local"].score == 1.0 and by_name["cloud"].score == 0.0
    assert by_name["local"].display == "1s"


def test_constraints_make_candidates_ineligible():
    recs, _ = DecisionEngine().decide(_pair(), constraints=[Constraint("cost", "<=", 1.0)],
                                      weights={"quality": 1})
    assert [r.strategy_name for r in recs] == ["local", "cloud"]
    assert recs[1].eligible is False and "cost" in recs[1].violated_constraints[0]
    none_ok, _ = DecisionEngine().decide(_pair(), constraints=[Constraint("quality", ">=", 2.0)])
    assert not any(r.eligible for r in none_ok)


def test_corpus_fit_rules():
    lang = {"primary_language": "gu", "is_multilingual": False, "structure_level": "flat", "code_line_ratio": 0.0}
    en_only, multi = _s("m", embedder="local_minilm"), _s("o", embedder="openai_text_embedding_3_small")
    assert corpus_fit(en_only, lang).score == 0.25 and corpus_fit(en_only, lang).warnings
    assert corpus_fit(multi, lang).score == 0.75

    code = {"primary_language": "en", "is_multilingual": False, "structure_level": "flat", "code_line_ratio": 0.5}
    assert corpus_fit(_s("c", chunker="code_aware"), code).score == 0.75
    assert corpus_fit(_s("f", chunker="fixed_size"), code).score == 0.25
    assert corpus_fit(_s("r"), code).score == 0.5

    md = {"structure_level": "structured", "code_line_ratio": 0.0, "primary_language": "en"}
    assert corpus_fit(_s("md", chunker="markdown_aware"), md).score == 0.75

    recs, weights = DecisionEngine().decide(_pair(), corpus_features=lang)
    assert "corpus_fit" in weights and recs[0].factor("corpus_fit") is not None


def test_corpus_warnings():
    assert corpus_warnings({}) == []
    w = corpus_warnings({"ocr_recommended": True, "scanned_doc_ratio": 0.5, "duplicate_doc_ratio": 0.3})
    assert len(w) == 2 and "50%" in w[0] and "30%" in w[1]


def test_quality_value():
    v, note = quality_value({"recall@3": 1.0, "mrr": 0.0, "ndcg@3": 0.0, "precision@3": 1.0})
    assert v == pytest.approx(0.4) and "precision" not in note
    assert quality_value({})[0] == 0.0


def test_invalid_inputs():
    with pytest.raises(InvalidDecisionError):
        DecisionEngine().decide([])
    for bad in ({"speed": 1}, {"quality": -1}, {"quality": 0, "latency": 0, "cost": 0}, {"corpus_fit": 1}):
        with pytest.raises(InvalidDecisionError):  # last one: only corpus_fit, but no features to score it
            DecisionEngine().decide(_pair(), weights=bad)
    with pytest.raises(ValueError):
        Constraint("speed", "<=", 1)
    with pytest.raises(ValueError):
        Constraint("cost", "<", 1)
    assert Constraint.from_dict({"metric": "cost", "operator": "<=", "value": "2"}).value == 2.0


def _decision(constraints=()):
    recs, weights = DecisionEngine().decide(_pair(), constraints=constraints, weights={"quality": 1})
    return Decision(experiment_id="e", dataset_id="d", weights=weights, constraints=list(constraints),
                    recommendations=recs, tradeoffs=TradeoffAnalyzer().analyze(recs), warnings=["careful"])


def test_decision_round_trip_and_explainers():
    d = _decision()
    assert Decision.from_dict(d.to_dict()).to_dict() == d.to_dict()
    text = TemplateExplainer().explain(d)
    assert "Recommended: cloud" in text and "Warning: careful" in text and "local is better" in text

    class Gen:
        def generate(self, query, results):
            assert "Recommended: cloud" in results[0].text
            return "  LLM says cloud.  "

    class Broken:
        def generate(self, query, results):
            raise RuntimeError("api down")

    assert LlmExplainer(Gen()).explain(d) == "LLM says cloud."
    assert LlmExplainer(Broken()).explain(d) == text

    none = _decision(constraints=[Constraint("quality", ">=", 2.0)])
    assert none.winner is None and "No strategy satisfied all constraints" in TemplateExplainer().explain(none)
