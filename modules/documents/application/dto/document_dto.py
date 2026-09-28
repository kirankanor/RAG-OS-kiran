from __future__ import annotations

from dataclasses import dataclass, field

from modules.documents.domain.entities.document import Document
from modules.documents.domain.entities.document_version import DocumentVersion


@dataclass
class DocumentVersionDTO:
    number: int = 0
    filename: str = ""
    content_hash: str = ""
    size_bytes: int = 0
    note: str = ""
    created_at: str = ""

    @classmethod
    def from_entity(cls, v: DocumentVersion) -> DocumentVersionDTO:
        return cls(number=v.number, filename=v.filename, content_hash=v.content_hash.value,
                   size_bytes=v.size_bytes, note=v.note, created_at=v.created_at)


@dataclass
class DocumentDTO:
    id: str = ""
    name: str = ""
    filename: str = ""
    status: str = ""
    current_version: int = 0
    content_hash: str = ""      # of the current version
    size_bytes: int = 0         # of the current version
    versions: list[DocumentVersionDTO] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    deleted_at: str = ""

    @classmethod
    def from_entity(cls, d: Document) -> DocumentDTO:
        cur = d.current_version
        return cls(id=str(d.id), name=d.name, filename=d.filename, status=d.status.value,
                   current_version=cur.number if cur else 0,
                   content_hash=cur.content_hash.value if cur else "",
                   size_bytes=cur.size_bytes if cur else 0,
                   versions=[DocumentVersionDTO.from_entity(v) for v in d.versions],
                   created_at=d.created_at, updated_at=d.updated_at, deleted_at=d.deleted_at)
