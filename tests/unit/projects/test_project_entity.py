import pytest

from modules.projects.domain.entities.project import Project
from modules.projects.domain.events.project_events import ProjectCreated, ProjectDeleted, ProjectUpdated
from modules.projects.domain.exceptions import InvalidProjectError, ProjectStateError
from modules.projects.domain.value_objects.project_id import ProjectId
from modules.projects.domain.value_objects.project_status import ProjectStatus


def _p(**kw):
    return Project.create("Demo", "u1", **kw)


def test_create_validates_and_dedupes():
    p = _p(document_ids=["d1", "d1", "", "d2"], experiment_ids=["e1"])
    assert p.name == "Demo" and p.document_ids == ["d1", "d2"] and p.status == ProjectStatus.ACTIVE
    assert [type(e) for e in p.pull_events()] == [ProjectCreated] and p.pull_events() == []
    with pytest.raises(InvalidProjectError) as e:
        Project.create("  ", "")
    assert len(e.value.errors) == 2
    with pytest.raises(ValueError):
        ProjectId("")


def test_updates_are_change_detected_and_emit_one_event_each():
    p = _p()
    p.pull_events()
    assert p.update(name="Demo", description="") is False            # nothing changed
    assert p.update(name=" New ", description="text") is True
    assert (p.name, p.description) == ("New", "text")
    assert p.add_documents(["d1", "d2", "d1"]) is True and p.add_documents(["d1"]) is False
    assert p.remove_documents(["d1", "zzz"]) is True and p.remove_documents(["d1"]) is False
    assert p.document_ids == ["d2"]
    assert p.add_experiments(["e1"]) and p.remove_experiments(["e1"]) and p.experiment_ids == []
    events = p.pull_events()
    assert all(isinstance(e, ProjectUpdated) for e in events)
    assert [e.changes for e in events] == [("name", "description"), ("documents",), ("documents",),
                                           ("experiments",), ("experiments",)]
    with pytest.raises(InvalidProjectError):
        p.update(name="  ")


def test_archived_is_read_only_and_deleted_is_frozen():
    p = _p(document_ids=["d1"])
    p.pull_events()
    assert p.archive() is True and p.archive() is False and p.is_archived
    for change in (lambda: p.update(name="x"), lambda: p.add_documents(["d9"]),
                   lambda: p.remove_documents(["d1"]), lambda: p.add_experiments(["e9"])):
        with pytest.raises(ProjectStateError):
            change()
    assert p.unarchive() is True and p.unarchive() is False
    assert p.add_documents(["d9"]) is True

    assert p.archive() and p.delete() is True and p.delete() is False and p.is_deleted   # archived -> deleted ok
    for change in (p.archive, p.unarchive, lambda: p.update(name="x")):
        with pytest.raises(ProjectStateError):
            change()
    assert isinstance(p.pull_events()[-1], ProjectDeleted) and p.deleted_at
