from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from modules.ingestion.domain.entities.ingestion_job import IngestionJob
from modules.ingestion.domain.value_objects.ingestion_status import IngestionStatus


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class IngestionRun:
    """Aggregate root for one ingestion invocation: a batch of source files
    submitted together, each tracked as an IngestionJob. Status is derived
    from job statuses rather than stored directly, so it can't drift out of
    sync with its jobs.

    Not the same concept as shared.infrastructure.database.db_models.RunRow /
    shared.domain.types.RunConfig, which track the full parser+chunker+
    embedder+retriever+reranker strategy choice for a pipeline experiment.
    This entity is scoped to ingestion progress only.
    """

    id: str = field(default_factory=_new_id)
    name: str = ""
    jobs: list[IngestionJob] = field(default_factory=list)
    created_at: str = field(default_factory=_utcnow)
    completed_at: str = ""

    @property
    def status(self) -> IngestionStatus:
        if not self.jobs:
            return IngestionStatus.PENDING
        statuses = {j.status for j in self.jobs}
        if statuses == {IngestionStatus.COMPLETED}:
            return IngestionStatus.COMPLETED
        if statuses and statuses <= {IngestionStatus.FAILED, IngestionStatus.COMPLETED} and IngestionStatus.FAILED in statuses:
            return IngestionStatus.FAILED
        if IngestionStatus.RUNNING in statuses or IngestionStatus.RETRYING in statuses:
            return IngestionStatus.RUNNING
        return IngestionStatus.PENDING

    def add_job(self, job: IngestionJob) -> None:
        job.run_id = self.id
        self.jobs.append(job)

    def mark_completed(self) -> None:
        self.completed_at = _utcnow()
