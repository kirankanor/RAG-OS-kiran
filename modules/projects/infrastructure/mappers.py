from __future__ import annotations

from modules.projects.domain.entities.project import Project
from modules.projects.domain.value_objects.project_id import ProjectId
from modules.projects.domain.value_objects.project_status import ProjectStatus
from modules.projects.infrastructure.persistence.models import ProjectRow
from shared.infrastructure.database.db_models import dumps, loads


def project_to_row(p: Project) -> ProjectRow:
    return ProjectRow(id=str(p.id), name=p.name, description=p.description, owner_id=p.owner_id,
                      status=p.status.value, document_ids_json=dumps(p.document_ids),
                      experiment_ids_json=dumps(p.experiment_ids), created_at=p.created_at,
                      updated_at=p.updated_at, deleted_at=p.deleted_at)


def row_to_project(row: ProjectRow) -> Project:
    return Project(id=ProjectId(row.id), name=row.name, description=row.description,
                   owner_id=row.owner_id, status=ProjectStatus(row.status),
                   document_ids=list(loads(row.document_ids_json) or []),
                   experiment_ids=list(loads(row.experiment_ids_json) or []),
                   created_at=row.created_at, updated_at=row.updated_at, deleted_at=row.deleted_at)
