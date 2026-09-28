import pytest

from modules.documents.domain.entities.document import Document
from modules.documents.domain.exceptions import DocumentNotFoundError
from modules.experiments.domain.exceptions import ExperimentNotFoundError
from modules.projects.application.services.project_service import ProjectService
from modules.projects.domain.events.project_events import ProjectCreated, ProjectDeleted, ProjectUpdated
from modules.projects.domain.exceptions import InvalidProjectError, ProjectNotFoundError, ProjectStateError
from modules.projects.domain.value_objects.project_status import ProjectStatus
from modules.users.domain.entities.user import User
from modules.users.domain.exceptions import UserNotFoundError


class _Users:
    def __init__(self):
        self.inactive = User(email="off@example.com", is_active=False)
        self.active = User(email="on@example.com")

    def get_user(self, user_id):
        for u in (self.inactive, self.active):
            if str(u.id) == user_id:
                return u
        raise UserNotFoundError(user_id)


class _Documents:
    def __init__(self):
        self.docs = {"d1": Document(), "d2": Document(), "dead": Document()}
        self.docs["dead"].delete()

    def get(self, document_id):
        if document_id not in self.docs:
            raise DocumentNotFoundError(document_id)
        return self.docs[document_id]


class _Experiments:
    def get(self, experiment_id):
        if experiment_id not in ("e1", "e2"):
            raise ExperimentNotFoundError(experiment_id)
        return object()


def _svc(events=None):
    users = _Users()
    svc = ProjectService(users=users, documents=_Documents(), experiments=_Experiments(),
                         publisher=events.append if events is not None else None)
    return svc, str(users.active.id), users


def test_create_update_archive_delete_flow(isolated_env):
    events = []
    svc, owner, _ = _svc(events)
    p = svc.create("Demo", owner, "desc", document_ids=["d1"], experiment_ids=["e1"])
    assert p.document_ids == ["d1"] and p.owner_id == owner
    assert svc.get(str(p.id)).document_ids == ["d1"]                       # DB round trip

    q = svc.update(str(p.id), name="Renamed", add_document_ids=["d2", "d1"], remove_experiment_ids=["e1"])
    assert q.name == "Renamed" and q.document_ids == ["d1", "d2"] and q.experiment_ids == []
    n_before = len(events)
    svc.update(str(p.id), name="Renamed")                                   # no-op: nothing saved or published
    assert len(events) == n_before

    a = svc.update(str(p.id), archived=True)
    assert a.status == ProjectStatus.ARCHIVED
    with pytest.raises(ProjectStateError):
        svc.update(str(p.id), name="nope")
    b = svc.update(str(p.id), archived=False, description="edited")        # unarchive + edit in one call
    assert b.status == ProjectStatus.ACTIVE and b.description == "edited"

    d = svc.delete(str(p.id))
    assert d.is_deleted and svc.delete(str(p.id)).is_deleted
    assert svc.list() == [] and [x.id for x in svc.list(statuses=[ProjectStatus.DELETED])] == [p.id]
    types = [type(e) for e in events]
    assert types[0] is ProjectCreated and types[-1] is ProjectDeleted and types.count(ProjectDeleted) == 1
    assert ProjectUpdated in types


def test_validation_collects_every_problem(isolated_env):
    svc, owner, users = _svc()
    with pytest.raises(InvalidProjectError) as e:
        svc.create("x", "ghost", document_ids=["d1", "nope", "dead"], experiment_ids=["e1", "nope"])
    assert len(e.value.errors) == 4                                        # owner, 2 docs, 1 experiment
    with pytest.raises(InvalidProjectError):
        svc.create("x", str(users.inactive.id))
    with pytest.raises(InvalidProjectError):
        svc.create("  ", owner)
    assert svc.list() == []                                                # nothing was saved

    p = svc.create("ok", owner, document_ids=["d1"])
    with pytest.raises(InvalidProjectError):
        svc.update(str(p.id), add_document_ids=["dead"])
    assert svc.get(str(p.id)).document_ids == ["d1"]                       # failed update changed nothing

    svc.documents.docs["d1"].delete()                                      # linked doc goes stale later
    svc.update(str(p.id), add_document_ids=["d1"], name="still fine")      # re-adding a linked id is not re-validated
    svc.update(str(p.id), remove_document_ids=["d1"])                      # and removing is always allowed
    assert svc.get(str(p.id)).document_ids == []
    with pytest.raises(ProjectNotFoundError):
        svc.get("nope")
    with pytest.raises(ProjectNotFoundError):
        svc.delete("nope")


def test_list_filters_by_owner_and_status(isolated_env):
    svc, owner, users = _svc()
    other = users.inactive
    other.activate()
    mine = svc.create("mine", owner)
    theirs = svc.create("theirs", str(other.id))
    svc.update(str(mine.id), archived=True)
    assert {p.id for p in svc.list()} == {mine.id, theirs.id}
    assert [p.id for p in svc.list(owner_id=owner)] == [mine.id]
    assert [p.id for p in svc.list(statuses=[ProjectStatus.ACTIVE])] == [theirs.id]
