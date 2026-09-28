from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence

from sqlmodel import SQLModel

from modules.documents.application.services.document_service import DocumentService
from modules.documents.domain.exceptions import DocumentNotFoundError
from modules.experiments.application.services.experiment_service import ExperimentService
from modules.experiments.domain.exceptions import ExperimentNotFoundError
from modules.projects.domain.entities.project import Project
from modules.projects.domain.events.project_events import ProjectEvent
from modules.projects.domain.exceptions import InvalidProjectError, ProjectNotFoundError
from modules.projects.domain.repositories.project_repository import ProjectRepository
from modules.projects.domain.value_objects.project_status import ProjectStatus
# Importing models registers the projects table on SQLModel.metadata.
from modules.projects.infrastructure.persistence import models as _models  # noqa: F401
from modules.projects.infrastructure.persistence.repository import SqlProjectRepository
from modules.users.application.services.user_service import UserService
from modules.users.domain.exceptions import UserNotFoundError
from shared.infrastructure.database.db_models import get_engine

EventPublisher = Callable[[ProjectEvent], None]


def _ensure_tables() -> None:
    SQLModel.metadata.create_all(get_engine())  # idempotent


class ProjectService:
    """Projects group an owner's documents and experiments by id. New links are checked
    against the users/documents/experiments services (owner must exist and be active,
    documents must exist and not be deleted, experiments must exist); a link that later
    goes stale (e.g. its document is deleted) is left alone, and removing links is never
    validated. There are no permission checks: owner_id is recorded and filterable, nothing more.
    Events go to `publisher` (if any) after the change is saved."""

    def __init__(self, repository: ProjectRepository | None = None, users: UserService | None = None,
                 documents: DocumentService | None = None, experiments: ExperimentService | None = None,
                 publisher: EventPublisher | None = None):
        _ensure_tables()
        self.repository = repository or SqlProjectRepository()
        self.users = users or UserService()
        self.documents = documents or DocumentService()
        self.experiments = experiments or ExperimentService()
        self.publisher = publisher

    def create(self, name: str, owner_id: str, description: str = "", document_ids: Iterable[str] = (),
               experiment_ids: Iterable[str] = ()) -> Project:
        project = Project.create(name, owner_id, description, document_ids, experiment_ids)
        self._raise_if_any(self._check_owner(owner_id) + self._check_documents(project.document_ids)
                           + self._check_experiments(project.experiment_ids))
        self.repository.save(project)
        self._publish(project)
        return project

    def update(self, project_id: str, name: str | None = None, description: str | None = None,
               add_document_ids: Sequence[str] = (), remove_document_ids: Sequence[str] = (),
               add_experiment_ids: Sequence[str] = (), remove_experiment_ids: Sequence[str] = (),
               archived: bool | None = None) -> Project:
        """`archived=False` unarchives first so the other edits apply; `archived=True`
        archives after them. Nothing is saved (or published) if nothing changed."""
        project = self.get(project_id)
        if archived is False:
            project.unarchive()
        new_docs = [i for i in add_document_ids if i not in project.document_ids]
        new_exps = [i for i in add_experiment_ids if i not in project.experiment_ids]
        self._raise_if_any(self._check_documents(new_docs) + self._check_experiments(new_exps))

        project.update(name, description)
        project.add_documents(add_document_ids)
        project.remove_documents(remove_document_ids)
        project.add_experiments(add_experiment_ids)
        project.remove_experiments(remove_experiment_ids)
        if archived is True:
            project.archive()
        if project.pending_events:
            self.repository.save(project)
            self._publish(project)
        return project

    def delete(self, project_id: str) -> Project:
        """Soft delete (idempotent)."""
        project = self.get(project_id)
        if project.delete():
            self.repository.save(project)
            self._publish(project)
        return project

    def get(self, project_id: str) -> Project:
        p = self.repository.get(project_id)
        if p is None:
            raise ProjectNotFoundError(f"No project with id '{project_id}'")
        return p

    def list(self, owner_id: str = "", statuses: Iterable[ProjectStatus] | None = None) -> list[Project]:
        """statuses=None lists active and archived projects."""
        return self.repository.list(owner_id, statuses)

    # --- internals ----------------------------------------------------------

    def _check_owner(self, owner_id: str) -> list[str]:
        try:
            user = self.users.get_user(owner_id)
        except UserNotFoundError:
            return [f"Owner '{owner_id}' does not exist."]
        return [] if user.is_active else [f"Owner '{owner_id}' is inactive."]

    def _check_documents(self, ids: Iterable[str]) -> list[str]:
        errors = []
        for i in ids:
            try:
                doc = self.documents.get(i)
            except DocumentNotFoundError:
                errors.append(f"Document '{i}' does not exist.")
                continue
            if doc.is_deleted:
                errors.append(f"Document '{i}' is deleted.")
        return errors

    def _check_experiments(self, ids: Iterable[str]) -> list[str]:
        errors = []
        for i in ids:
            try:
                self.experiments.get(i)
            except ExperimentNotFoundError:
                errors.append(f"Experiment '{i}' does not exist.")
        return errors

    @staticmethod
    def _raise_if_any(errors: list[str]) -> None:
        if errors:
            raise InvalidProjectError("Invalid project: " + "; ".join(errors), errors)

    def _publish(self, project: Project) -> None:
        events = project.pull_events()
        if self.publisher:
            for event in events:
                self.publisher(event)
