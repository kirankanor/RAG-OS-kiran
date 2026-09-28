from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime

from modules.projects.domain.events.project_events import (
    ProjectCreated, ProjectDeleted, ProjectEvent, ProjectUpdated,
)
from modules.projects.domain.exceptions import InvalidProjectError, ProjectStateError
from modules.projects.domain.value_objects.project_id import ProjectId
from modules.projects.domain.value_objects.project_status import ProjectStatus


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _dedupe(ids: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for i in ids:
        if i and i not in seen:
            seen.add(i)
            out.append(i)
    return out


@dataclass
class Project:
    """Aggregate root: the container tying an owner (user id) to documents and experiments.
    Holds ids only; the referenced things live in their own modules and are checked by the
    service. Archived projects are read-only, deleted ones are frozen. State changes queue
    domain events in `pending_events` (never persisted); the service publishes them."""

    id: ProjectId = field(default_factory=ProjectId.new)
    name: str = ""
    description: str = ""
    owner_id: str = ""
    status: ProjectStatus = ProjectStatus.ACTIVE
    document_ids: list[str] = field(default_factory=list)
    experiment_ids: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_utcnow)
    updated_at: str = field(default_factory=_utcnow)
    deleted_at: str = ""
    pending_events: list[ProjectEvent] = field(default_factory=list, repr=False, compare=False)

    @classmethod
    def create(cls, name: str, owner_id: str, description: str = "", document_ids: Iterable[str] = (),
               experiment_ids: Iterable[str] = ()) -> Project:
        errors = []
        if not name.strip():
            errors.append("Project name is required.")
        if not owner_id:
            errors.append("owner_id is required.")
        if errors:
            raise InvalidProjectError("Invalid project: " + " ".join(errors), errors)
        p = cls(name=name.strip(), description=description, owner_id=owner_id,
                document_ids=_dedupe(document_ids), experiment_ids=_dedupe(experiment_ids))
        p.pending_events.append(ProjectCreated(project_id=str(p.id), owner_id=owner_id))
        return p

    @property
    def is_deleted(self) -> bool:
        return self.status == ProjectStatus.DELETED

    @property
    def is_archived(self) -> bool:
        return self.status == ProjectStatus.ARCHIVED

    def _ensure_editable(self) -> None:
        if self.is_deleted:
            raise ProjectStateError("Project is deleted.")
        if self.is_archived:
            raise ProjectStateError("Project is archived; unarchive it before changing it.")

    def _changed(self, *fields: str) -> bool:
        self.updated_at = _utcnow()
        self.pending_events.append(ProjectUpdated(project_id=str(self.id), changes=tuple(fields)))
        return True

    def update(self, name: str | None = None, description: str | None = None) -> bool:
        """Returns False if nothing actually changed."""
        self._ensure_editable()
        changed: list[str] = []
        if name is not None:
            if not name.strip():
                raise InvalidProjectError("Project name is required.")
            if name.strip() != self.name:
                self.name = name.strip()
                changed.append("name")
        if description is not None and description != self.description:
            self.description = description
            changed.append("description")
        return self._changed(*changed) if changed else False

    def add_documents(self, ids: Iterable[str]) -> bool:
        self._ensure_editable()
        new = [i for i in _dedupe(ids) if i not in self.document_ids]
        self.document_ids.extend(new)
        return self._changed("documents") if new else False

    def remove_documents(self, ids: Iterable[str]) -> bool:
        self._ensure_editable()
        drop = set(ids) & set(self.document_ids)
        self.document_ids = [i for i in self.document_ids if i not in drop]
        return self._changed("documents") if drop else False

    def add_experiments(self, ids: Iterable[str]) -> bool:
        self._ensure_editable()
        new = [i for i in _dedupe(ids) if i not in self.experiment_ids]
        self.experiment_ids.extend(new)
        return self._changed("experiments") if new else False

    def remove_experiments(self, ids: Iterable[str]) -> bool:
        self._ensure_editable()
        drop = set(ids) & set(self.experiment_ids)
        self.experiment_ids = [i for i in self.experiment_ids if i not in drop]
        return self._changed("experiments") if drop else False

    def archive(self) -> bool:
        if self.is_deleted:
            raise ProjectStateError("Project is deleted.")
        if self.is_archived:
            return False
        self.status = ProjectStatus.ARCHIVED
        return self._changed("status")

    def unarchive(self) -> bool:
        if self.is_deleted:
            raise ProjectStateError("Project is deleted.")
        if not self.is_archived:
            return False
        self.status = ProjectStatus.ACTIVE
        return self._changed("status")

    def delete(self) -> bool:
        """Soft delete (allowed from active or archived). Returns False if already deleted."""
        if self.is_deleted:
            return False
        self.status = ProjectStatus.DELETED
        self.deleted_at = self.updated_at = _utcnow()
        self.pending_events.append(ProjectDeleted(project_id=str(self.id)))
        return True

    def pull_events(self) -> list[ProjectEvent]:
        events, self.pending_events = self.pending_events, []
        return events
