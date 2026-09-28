import pytest

from modules.documents.application.services.document_service import DocumentService
from modules.experiments.application.services.experiment_service import ExperimentService
from modules.projects.application.commands.create_project import CreateProjectCommand
from modules.projects.application.commands.delete_project import DeleteProjectCommand
from modules.projects.application.commands.update_project import UpdateProjectCommand
from modules.projects.application.queries.get_project import GetProjectQuery
from modules.projects.application.queries.list_projects import ListProjectsQuery
from modules.projects.domain.exceptions import InvalidProjectError, ProjectStateError
from modules.users.application.services.user_service import UserService
# Importing this also registers the test_hash embedder / test_bruteforce retriever.
from tests.integration.test_smoke_experiments import _config, _strategy


def test_project_with_real_users_documents_and_experiments(isolated_env):
    owner = UserService().register("owner@example.com", "password123")
    docs = DocumentService()
    d1 = docs.upload("Cats", "cats.txt", b"Cats purr and sleep all day.")
    d2 = docs.upload("Rockets", "rockets.txt", b"Rockets burn fuel to reach orbit.")
    exps = ExperimentService()
    exp = exps.create("cmp", _config(isolated_env), [str(_strategy("s1").id)])

    created = CreateProjectCommand().execute("Demo", str(owner.id), description="first",
                                             document_ids=[str(d1.id)], experiment_ids=[str(exp.id)])
    assert created.status == "active" and created.num_documents == 1 and created.num_experiments == 1
    assert GetProjectQuery().execute(created.id).document_ids == [str(d1.id)]       # survives the DB
    assert [p.id for p in ListProjectsQuery().execute(owner_id=str(owner.id))] == [created.id]

    updated = UpdateProjectCommand().execute(created.id, name="Demo 2", add_document_ids=[str(d2.id)])
    assert updated.name == "Demo 2" and updated.document_ids == [str(d1.id), str(d2.id)]

    docs.delete(str(d1.id))                                                        # stale link stays
    assert GetProjectQuery().execute(created.id).num_documents == 2
    with pytest.raises(InvalidProjectError):                                        # but new links are checked
        UpdateProjectCommand().execute(created.id, add_document_ids=[str(d1.id), "nope"])
    with pytest.raises(InvalidProjectError):
        CreateProjectCommand().execute("Bad", "no-such-user")
    with pytest.raises(InvalidProjectError):
        CreateProjectCommand().execute("Bad", str(owner.id), experiment_ids=["no-such-experiment"])

    assert UpdateProjectCommand().execute(created.id, archived=True).status == "archived"
    with pytest.raises(ProjectStateError):
        UpdateProjectCommand().execute(created.id, name="blocked")

    gone = DeleteProjectCommand().execute(created.id)
    assert gone.status == "deleted"
    assert ListProjectsQuery().execute() == []
    assert [p.id for p in ListProjectsQuery().execute(include_deleted=True)] == [created.id]
    assert docs.get(str(d2.id)).is_deleted is False                                 # deleting a project leaves documents alone
