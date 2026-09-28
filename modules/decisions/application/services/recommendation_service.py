from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from sqlmodel import SQLModel

from modules.corpus_analysis.application.services.corpus_analysis_service import CorpusAnalysisService
from modules.decisions.application.services.decision_engine import CandidateInput, DecisionEngine
from modules.decisions.application.services.tradeoff_analyzer import TradeoffAnalyzer
from modules.decisions.domain.entities.decision import Decision
from modules.decisions.domain.exceptions import DecisionNotFoundError, InvalidDecisionError
from modules.decisions.domain.models.constraint import Constraint
from modules.decisions.domain.rules.quality_rules import corpus_warnings
from modules.decisions.infrastructure.llm.decision_explainer import (
    DecisionExplainer, LlmExplainer, TemplateExplainer,
)
# Importing models registers the decisions table on SQLModel.metadata.
from modules.decisions.infrastructure.persistence import models as _models  # noqa: F401
from modules.decisions.infrastructure.persistence.repository import DecisionRepository
from modules.evaluation.application.services.evaluation_service import EvaluationService
from modules.evaluation.domain.entities.evaluation_run import EvaluationStatus
from modules.experiments.application.services.experiment_service import ExperimentService
from modules.experiments.domain.value_objects.experiment_status import ExperimentStatus
from modules.strategies.application.services.strategy_service import StrategyService
from shared.ai.llm import generator_registry
from shared.infrastructure.database.db_models import get_engine


def _ensure_tables() -> None:
    SQLModel.metadata.create_all(get_engine())  # idempotent


class RecommendationService:
    """Turns a finished, evaluated experiment into a persisted Decision: gathers each
    strategy's evaluation metrics and run time (and optionally a corpus profile), scores
    them with the DecisionEngine, finds trade-offs and writes an explanation."""

    def __init__(self, repository: DecisionRepository | None = None, engine: DecisionEngine | None = None,
                 analyzer: TradeoffAnalyzer | None = None, experiments: ExperimentService | None = None,
                 evaluation: EvaluationService | None = None, strategies: StrategyService | None = None,
                 corpus: CorpusAnalysisService | None = None):
        _ensure_tables()
        self.repository = repository or DecisionRepository()
        self.engine = engine or DecisionEngine()
        self.analyzer = analyzer or TradeoffAnalyzer()
        self.experiments = experiments or ExperimentService()
        self.evaluation = evaluation or EvaluationService()
        self.strategies = strategies or StrategyService()
        self.corpus = corpus or CorpusAnalysisService()

    def make_decision(self, experiment_id: str, dataset_id: str, corpus_profile_id: str = "",
                      weights: Mapping[str, float] | None = None,
                      constraints: Sequence[Constraint | dict[str, Any]] | None = None,
                      explain_with: str = "") -> Decision:
        """`weights` overrides the defaults and is taken as complete (missing factor = 0).
        `explain_with` is a generator name from the generator registry (e.g. 'groq_chat');
        empty uses the deterministic template explanation."""
        explainer = self._explainer(explain_with)
        parsed = self._constraints(constraints)

        experiment = self.experiments.get(experiment_id)  # raises ExperimentNotFoundError
        evaluations = [e for e in self.evaluation.compare(dataset_id, experiment_id)
                       if e.status == EvaluationStatus.COMPLETED]
        if not evaluations:
            raise InvalidDecisionError(
                f"No completed evaluations of experiment '{experiment_id}' on dataset '{dataset_id}'. "
                "Run the evaluation first.")
        runs = {r.id: r for r in experiment.runs}
        candidates = []
        for ev in evaluations:
            run = runs.get(ev.experiment_run_id)
            latency = run.duration_seconds if run and run.status == ExperimentStatus.COMPLETED else None
            candidates.append(CandidateInput(strategy=self.strategies.get(ev.strategy_id, ev.strategy_version),
                                             quality_metrics=ev.result.summary(), latency_seconds=latency))

        features = self.corpus.get_profile(corpus_profile_id).features() if corpus_profile_id else None
        recommendations, used_weights = self.engine.decide(candidates, parsed, features, weights)
        decision = Decision(
            experiment_id=experiment_id, dataset_id=dataset_id, corpus_profile_id=corpus_profile_id,
            weights=used_weights, constraints=parsed, recommendations=recommendations,
            tradeoffs=self.analyzer.analyze(recommendations),
            warnings=corpus_warnings(features) if features else [])
        decision.explanation = explainer.explain(decision)
        self.repository.save(decision)
        return decision

    def get(self, decision_id: str) -> Decision:
        d = self.repository.get(decision_id)
        if d is None:
            raise DecisionNotFoundError(f"No decision with id '{decision_id}'")
        return d

    def list(self, experiment_id: str = "") -> list[Decision]:
        return self.repository.list(experiment_id)

    @staticmethod
    def _explainer(explain_with: str) -> DecisionExplainer:
        if not explain_with:
            return TemplateExplainer()
        if explain_with not in generator_registry.names():
            raise InvalidDecisionError(
                f"Unknown generator '{explain_with}'. Available: {generator_registry.names()}")
        return LlmExplainer(generator_registry.create(explain_with))

    @staticmethod
    def _constraints(raw: Sequence[Constraint | dict[str, Any]] | None) -> list[Constraint]:
        out: list[Constraint] = []
        for c in raw or []:
            try:
                out.append(c if isinstance(c, Constraint) else Constraint.from_dict(c))
            except (ValueError, KeyError, TypeError) as e:
                raise InvalidDecisionError(f"Invalid constraint {c!r}: {e}") from e
        return out
