from __future__ import annotations

from collections.abc import Callable
from typing import Any

from modules.ingestion.domain.entities.ingestion_job import IngestionJob
from modules.ingestion.domain.exceptions import IngestionJobFailedError
from modules.ingestion.domain.value_objects.processing_stage import ProcessingStage


class StageRunner:
    """Runs one pipeline stage for a job: records the stage on the job, then
    executes the stage function. Any exception is wrapped in
    IngestionJobFailedError carrying the job id and failing stage, so callers
    only ever have to handle one failure type."""

    def run(self, job: IngestionJob, stage: ProcessingStage, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        job.advance(stage)
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            raise IngestionJobFailedError(
                f"{stage.value} failed: {e}", job_id=job.id, stage=stage.value
            ) from e
