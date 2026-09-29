from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from modules.artifacts.application.services.artifact_service import ArtifactService
from modules.artifacts.domain.entities.artifact import Artifact
from modules.artifacts.domain.value_objects.artifact_type import ArtifactType
from modules.artifacts.infrastructure.generators.code_generator import (
    generate_strategy_script, slugify,
)
from modules.artifacts.infrastructure.generators.markdown_generator import render_decision_report
from modules.artifacts.infrastructure.generators.zip_generator import build_zip
from modules.decisions.application.services.recommendation_service import RecommendationService
from modules.documents.application.services.document_service import DocumentService
from modules.documents.domain.exceptions import (
    DocumentNotFoundError, DocumentStorageError, DocumentVersionNotFoundError,
)
from modules.experiments.application.services.experiment_service import ExperimentService
from modules.experiments.domain.entities.experiment import Experiment
from modules.experiments.domain.exceptions import ExperimentNotFoundError
from modules.projects.application.dto.project_dto import ProjectDTO
from modules.projects.application.services.project_service import ProjectService
from modules.strategies.application.services.strategy_service import StrategyService
from modules.strategies.domain.exceptions import StrategyNotFoundError


def _json(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False, default=str)


def _experiment_dict(e: Experiment) -> dict[str, Any]:
    return {"id": str(e.id), "name": e.name, "description": e.description, "status": e.status.value,
            "config": e.config.to_dict(), "strategies": [r.to_dict() for r in e.strategy_refs],
            "runs": [{"strategy_id": r.strategy_id, "strategy_version": r.strategy_version,
                      "status": r.status.value, "duration_seconds": r.duration_seconds,
                      "pipeline_run_id": r.pipeline_run_id, "error_message": r.error_message}
                     for r in e.runs],
            "created_at": e.created_at, "completed_at": e.completed_at}


class PackageService:
    """Bundles a project's results into one zip: project.json, each experiment's config and
    run outcomes, a report per saved decision, a script per strategy used, optionally the
    documents' current files. Stale links (deleted/missing things) are skipped and noted."""

    def __init__(self, artifacts: ArtifactService | None = None, projects: ProjectService | None = None,
                 experiments: ExperimentService | None = None,
                 decisions: RecommendationService | None = None,
                 strategies: StrategyService | None = None, documents: DocumentService | None = None):
        self.artifacts = artifacts or ArtifactService()
        self.projects = projects or ProjectService()
        self.experiments = experiments or ExperimentService()
        self.decisions = decisions or RecommendationService()
        self.strategies = strategies or StrategyService()
        self.documents = documents or DocumentService()

    def package_project(self, project_id: str, include_documents: bool = False) -> Artifact:
        project = self.projects.get(project_id)  # raises ProjectNotFoundError
        files: dict[str, str | bytes] = {"project.json": _json(asdict(ProjectDTO.from_entity(project)))}
        notes: list[str] = []
        used: dict[tuple[str, int | None], None] = {}

        for exp_id in project.experiment_ids:
            try:
                exp = self.experiments.get(exp_id)
            except ExperimentNotFoundError:
                notes.append(f"Experiment '{exp_id}' no longer exists; skipped.")
                continue
            files[f"experiments/{exp_id}/experiment.json"] = _json(_experiment_dict(exp))
            used.update({(r.strategy_id, r.version): None for r in exp.strategy_refs})
            for d in self.decisions.list(exp_id):
                files[f"reports/decision-{d.id}.md"] = render_decision_report(d)

        for sid, version in used:
            try:
                s = self.strategies.get(sid, version)
            except StrategyNotFoundError:
                notes.append(f"Strategy '{sid}' v{version} not found; skipped.")
                continue
            name = f"{slugify(s.name, 'strategy')}_{sid}_v{s.version.number}.py"
            files[f"code/{name}"] = generate_strategy_script(s, name)

        if include_documents:
            for doc_id in project.document_ids:
                try:
                    doc = self.documents.get(doc_id)
                    if doc.is_deleted:
                        notes.append(f"Document '{doc_id}' is deleted; skipped.")
                        continue
                    files[f"documents/{doc_id}/{doc.filename}"] = self.documents.read_bytes(doc_id)
                except (DocumentNotFoundError, DocumentVersionNotFoundError, DocumentStorageError) as e:
                    notes.append(f"Document '{doc_id}' skipped: {e}")

        files["README.md"] = self._readme(project.name, project.description, str(project.id),
                                          sorted(files), notes)
        return self.artifacts.record(
            ArtifactType.PACKAGE, f"{project.name} package", f"{slugify(project.name, 'project')}-package.zip",
            build_zip(files), source_type="project", source_id=str(project.id))

    @staticmethod
    def _readme(name: str, description: str, project_id: str, paths: list[str], notes: list[str]) -> str:
        lines = [f"# {name}", ""]
        if description.strip():
            lines += [description.strip(), ""]
        lines += [f"Packaged from RAG-OS project `{project_id}`.", "", "## Contents", ""]
        lines += [f"- `{p}`" for p in paths] + ["- `README.md`", ""]
        if notes:
            lines += ["## Notes", ""] + [f"- {n}" for n in notes] + [""]
        return "\n".join(lines)
