import hashlib

import pytest

from modules.documents.application.commands.create_version import CreateVersionCommand
from modules.documents.application.commands.delete_document import DeleteDocumentCommand
from modules.documents.application.commands.upload_document import UploadDocumentCommand
from modules.documents.application.queries.get_document import GetDocumentQuery
from modules.documents.application.queries.list_documents import ListDocumentsQuery
from modules.documents.application.services.document_service import DocumentService
from modules.documents.domain.events.document_events import (
    DocumentDeleted, DocumentUploaded, DocumentVersionCreated,
)
from modules.documents.domain.exceptions import (
    DocumentNotFoundError, DocumentStateError, DocumentStorageError, DocumentVersionNotFoundError,
    DuplicateDocumentError, InvalidDocumentError, UnchangedContentError, UnsupportedDocumentTypeError,
)

V1, V2 = b"Cats purr and sleep all day.", b"Cats purr and sleep all day. Rockets burn fuel."


def test_upload_version_delete_flow(isolated_env):
    events = []
    svc = DocumentService(publisher=events.append)
    dto = UploadDocumentCommand(svc).execute("Cats", "cats.txt", V1, note="first")

    assert dto.current_version == 1 and dto.status == "active" and dto.name == "Cats"
    assert dto.content_hash == hashlib.sha256(V1).hexdigest() and dto.size_bytes == len(V1)
    q = GetDocumentQuery(svc)
    assert q.file_path(dto.id).read_bytes() == V1

    v2 = CreateVersionCommand(svc).execute(dto.id, V2, note="added rockets")
    assert v2.current_version == 2 and len(v2.versions) == 2 and v2.content_hash != dto.content_hash
    assert q.file_path(dto.id).read_bytes() == V2                  # current = v2
    assert q.file_path(dto.id, 1).read_bytes() == V1               # history intact
    assert q.version(dto.id, 1).note == "first" and q.version(dto.id).number == 2
    with pytest.raises(UnchangedContentError):
        CreateVersionCommand(svc).execute(dto.id, V2)
    with pytest.raises(DocumentVersionNotFoundError):
        q.version(dto.id, 9)

    gone = DeleteDocumentCommand(svc).execute(dto.id)
    assert gone.status == "deleted" and gone.deleted_at
    assert DeleteDocumentCommand(svc).execute(dto.id).status == "deleted"   # idempotent
    assert ListDocumentsQuery(svc).execute() == []
    assert [d.id for d in ListDocumentsQuery(svc).execute(include_deleted=True)] == [dto.id]
    with pytest.raises(DocumentStateError):
        CreateVersionCommand(svc).execute(dto.id, b"new content")
    assert q.file_path(dto.id, 1).read_bytes() == V1                        # files kept after soft delete

    assert [type(e) for e in events] == [DocumentUploaded, DocumentVersionCreated, DocumentDeleted]


def test_persistence_survives_a_new_service(isolated_env):
    svc = DocumentService()
    d = svc.upload("Cats", "cats.txt", V1)
    svc.create_version(str(d.id), V2)
    again = DocumentService().get(str(d.id))                         # fresh service, same DB
    assert [v.number for v in again.versions] == [1, 2]
    assert again.current_version.content_hash.value == hashlib.sha256(V2).hexdigest()
    assert again.pending_events == []                               # loading never creates events
    found = DocumentService().repository.find_by_content_hash(hashlib.sha256(V1).hexdigest())
    assert [x.id for x in found] == [d.id]                           # old versions are searchable too


def test_duplicate_content_rules(isolated_env):
    svc = DocumentService()
    a = svc.upload("A", "a.txt", V1)
    with pytest.raises(DuplicateDocumentError) as e:
        svc.upload("B", "b.txt", V1)
    assert e.value.existing_document_id == str(a.id)
    b = svc.upload("B", "b.txt", V1, allow_duplicate=True)          # explicit override
    svc.create_version(str(a.id), V2)                               # A's old V1 no longer counts...
    with pytest.raises(DuplicateDocumentError):                     # ...but B still holds V1 as current
        svc.upload("C", "c.txt", V1)
    svc.delete(str(b.id))                                           # deleted documents don't count either
    assert svc.upload("C", "c.txt", V1).current_version.number == 1


def test_validation_and_safety(isolated_env):
    svc = DocumentService(max_size_bytes=10)
    with pytest.raises(UnsupportedDocumentTypeError):
        svc.upload("x", "weird.xyz", b"data")
    with pytest.raises(InvalidDocumentError):
        svc.upload("x", "a.txt", b"")
    with pytest.raises(InvalidDocumentError):
        svc.upload("x", "a.txt", b"12345678901")                    # 11 bytes > 10
    with pytest.raises(InvalidDocumentError):
        svc.upload("x", "  ", b"data")
    with pytest.raises(DocumentNotFoundError):
        svc.get("nope")
    with pytest.raises(DocumentNotFoundError):
        svc.delete("nope")

    d = svc.upload("", "../../evil.txt", b"data")                   # traversal is stripped, name falls back
    assert d.name == "evil.txt" and d.filename == "evil.txt"
    path = svc.file_path(str(d.id))
    assert svc.blobs.root.resolve() in path.resolve().parents
    path.unlink()
    with pytest.raises(DocumentStorageError):
        svc.file_path(str(d.id))


def test_new_version_can_change_extension(isolated_env):
    svc = DocumentService()
    d = svc.upload("Doc", "doc.txt", V1)
    d2 = svc.create_version(str(d.id), b"# Title\n\nbody", filename="doc.md")
    assert d2.filename == "doc.md" and d2.version(1).filename == "doc.txt"
