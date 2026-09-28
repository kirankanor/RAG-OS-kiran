from __future__ import annotations

from sqlmodel import SQLModel

from modules.evaluation.application.services.metric_service import MetricService
from modules.evaluation.domain.entities.evaluation_dataset import EvaluationDataset, EvaluationQuery
from modules.evaluation.domain.entities.evaluation_run import EvaluationRun, EvaluationStatus
from modules.evaluation.domain.exceptions import (
    DatasetNotFoundError, EvaluationError, EvaluationRunNotFoundError, EvaluationStateError,
    InvalidDatasetError,
)
from modules.evaluation.domain.models.evaluation_result import EvaluationResult
# Importing models registers the evaluation tables on SQLModel.metadata.
from modules.evaluation.infrastructure.persistence import models as _models  # noqa: F401
from modules.evaluation.infrastructure.persistence.repository import EvaluationRepository
from modules.experiments.application.services.experiment_service import ExperimentService
from modules.experiments.domain.entities.experiment_run import ExperimentRun
from modules.experiments.domain.value_objects.experiment_status import ExperimentStatus
from shared.infrastructure.database.db_models import get_engine


def _ensure_tables() -> None:
    SQLModel.metadata.create_all(get_engine())  # idempotent


class EvaluationService:
    def __init__(self, repository: EvaluationRepository | None = None,
                 metrics: MetricService | None = None,
                 experiments: ExperimentService | None = None):
        _ensure_tables()
        self.repository = repository or EvaluationRepository()
        self.metrics = metrics or MetricService()
        self.experiments = experiments or ExperimentService()

    # --- datasets -----------------------------------------------------------

    def create_dataset(self, name: str, queries: list[EvaluationQuery | dict],
                       description: str = "") -> EvaluationDataset:
        qs = [q if isinstance(q, EvaluationQuery) else EvaluationQuery.from_dict(q) for q in queries]
        dataset = EvaluationDataset(name=name.strip(), description=description, queries=qs)
        errors = dataset.validation_errors()
        if errors:
            raise InvalidDatasetError("Invalid dataset: " + "; ".join(errors), errors)
        self.repository.save_dataset(dataset)
        return dataset

    def get_dataset(self, dataset_id: str) -> EvaluationDataset:
        d = self.repository.get_dataset(dataset_id)
        if d is None:
            raise DatasetNotFoundError(f"No evaluation dataset with id '{dataset_id}'")
        return d

    def list_datasets(self) -> list[EvaluationDataset]:
        return self.repository.list_datasets()

    # --- evaluation ---------------------------------------------------------

    def evaluate(self, dataset_id: str, experiment_id: str, k: int | None = None) -> list[EvaluationRun]:
        """Score every COMPLETED run of a finished experiment against the dataset.
        Runs that cannot be scored (e.g. ingestion runner, no matching queries) are
        recorded as FAILED evaluation runs. Non-completed experiment runs are skipped."""
        dataset = self.get_dataset(dataset_id)
        experiment = self.experiments.get(experiment_id)  # raises ExperimentNotFoundError
        if not experiment.status.is_terminal:
            raise EvaluationStateError(
                f"Experiment is {experiment.status.value}; evaluate after it has finished.")
        if k is not None and k < 1:
            raise EvaluationError("k must be >= 1.")
        out: list[EvaluationRun] = []
        for r in experiment.runs:
            if r.status != ExperimentStatus.COMPLETED:
                continue
            run = EvaluationRun(dataset_id=dataset.id, experiment_id=experiment_id,
                                experiment_run_id=r.id, strategy_id=r.strategy_id,
                                strategy_version=r.strategy_version,
                                pipeline_run_id=r.pipeline_run_id)
            try:
                run.complete(self._score(dataset, r, k))
            except EvaluationError as e:
                run.fail(str(e))
            self.repository.save_run(run)
            out.append(run)
        return out

    def _score(self, dataset: EvaluationDataset, r: ExperimentRun, k: int | None) -> EvaluationResult:
        by_query = r.result.get("queries")
        if not by_query:
            raise EvaluationError("Run has no retrieval results (was the runner 'ingestion'?).")
        eff_k = k or r.result.get("top_k") or 5
        common = [q for q in dataset.queries if q.query in by_query]
        if not common:
            raise EvaluationError("None of the dataset's queries appear in this run's results.")
        ids = [item["chunk_id"] for q in common for item in by_query[q.query]]
        full = self.repository.chunk_texts(r.pipeline_run_id, ids)  # falls back to stored text[:200]
        ranked = {q.query: [full.get(item["chunk_id"], item.get("text", ""))
                            for item in sorted(by_query[q.query], key=lambda x: x["rank"])]
                  for q in common}
        return self.metrics.evaluate(common, ranked, eff_k)

    # --- reading ------------------------------------------------------------

    def get_run(self, evaluation_run_id: str) -> EvaluationRun:
        run = self.repository.get_run(evaluation_run_id)
        if run is None:
            raise EvaluationRunNotFoundError(f"No evaluation run with id '{evaluation_run_id}'")
        return run

    def list_runs(self, dataset_id: str = "", experiment_id: str = "") -> list[EvaluationRun]:
        return self.repository.list_runs(dataset_id, experiment_id)

    def compare(self, dataset_id: str, experiment_id: str, sort_by: str = "mrr") -> list[EvaluationRun]:
        """Latest evaluation per experiment run, best first by `sort_by`
        (metric kind like 'mrr', 'recall', 'ndcg' or a full name like 'recall@3').
        Failed evaluations sort last."""
        self.get_dataset(dataset_id)
        latest: dict[str, EvaluationRun] = {}
        for r in self.repository.list_runs(dataset_id, experiment_id):  # oldest first
            latest[r.experiment_run_id] = r

        def score(r: EvaluationRun) -> float:
            if r.status != EvaluationStatus.COMPLETED:
                return -1.0
            for name, value in r.result.summary().items():
                if name == sort_by or name.startswith(sort_by + "@"):
                    return value
            return -1.0

        return sorted(latest.values(), key=score, reverse=True)
