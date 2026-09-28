from __future__ import annotations

from dataclasses import dataclass, field

from modules.projects.domain.entities.project import Project


@dataclass
class ProjectDTO:
    id: str = ""
    name: str = ""
    description: str = ""
    owner_id: str = ""
    status: str = ""
    document_ids: list[str] = field(default_factory=list)
    experiment_ids: list[str] = field(default_factory=list)
    num_documents: int = 0
    num_experiments: int = 0
    created_at: str = ""
    updated_at: str = ""
    deleted_at: str = ""

    @classmethod
    def from_entity(cls, p: Project) -> ProjectDTO:
        return cls(id=str(p.id), name=p.name, description=p.description, owner_id=p.owner_id,
                   status=p.status.value, document_ids=list(p.document_ids),
                   experiment_ids=list(p.experiment_ids), num_documents=len(p.document_ids),
                   num_experiments=len(p.experiment_ids), created_at=p.created_at,
                   updated_at=p.updated_at, deleted_at=p.deleted_at)
