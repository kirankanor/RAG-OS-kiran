import pytest

from modules.documents.domain.entities.document import Document
from modules.documents.domain.entities.document_version import DocumentVersion
from modules.documents.domain.events.document_events import (
    DocumentDeleted, DocumentUploaded, DocumentVersionCreated,
)
from modules.documents.domain.exceptions import DocumentStateError, InvalidDocumentError
from modules.documents.domain.value_objects.document_hash import DocumentHash
from modules.documents.domain.value_objects.document_id import DocumentId


def _v(n, data=b"x"):
    return DocumentVersion(number=n, content_hash=DocumentHash.from_bytes(data + bytes([n])),
                           size_bytes=len(data), filename="a.txt", storage_key=f"d/v{n}/a.txt")


def test_hash_validation_and_short():
    h = DocumentHash.from_bytes(b"hello")
    assert h.value == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    assert h.short == h.value[:12] and str(h) == h.value
    for bad in ("", "abc", "G" * 64, h.value.upper()):
        with pytest.raises(ValueError):
            DocumentHash(bad)
    with pytest.raises(ValueError):
        DocumentId("")


def test_versions_are_sequential_and_queue_events():
    d = Document(name="n")
    with pytest.raises(InvalidDocumentError):
        d.add_version(_v(2))                       # must start at 1
    d.add_version(_v(1))
    d.add_version(_v(2))
    with pytest.raises(InvalidDocumentError):
        d.add_version(_v(2))                       # no repeats
    assert d.current_version.number == 2 and d.version(1).number == 1 and d.version(9) is None
    assert d.filename == "a.txt"
    events = d.pull_events()
    assert [type(e) for e in events] == [DocumentUploaded, DocumentVersionCreated]
    assert [e.version for e in events] == [1, 2] and d.pull_events() == []


def test_delete_is_soft_idempotent_and_blocks_versions():
    d = Document(name="n")
    d.add_version(_v(1))
    d.pull_events()
    assert d.delete() is True and d.is_deleted and d.deleted_at
    assert d.delete() is False
    assert [type(e) for e in d.pull_events()] == [DocumentDeleted]
    with pytest.raises(DocumentStateError):
        d.add_version(_v(2))
    assert len(d.versions) == 1                    # history kept


def test_version_validation():
    with pytest.raises(ValueError):
        DocumentVersion(number=0, content_hash=DocumentHash.from_bytes(b"x"), size_bytes=1,
                        filename="a.txt", storage_key="k")
