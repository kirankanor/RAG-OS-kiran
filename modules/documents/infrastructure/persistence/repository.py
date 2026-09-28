from __future__ import annotations

from sqlmodel import col, select

from modules.documents.domain.entities.document import Document
from modules.documents.domain.entities.document_version import DocumentVersion
from modules.documents.domain.repositories.document_repository import DocumentRepository
from modules.documents.domain.value_objects.document_hash import DocumentHash
from modules.documents.domain.value_objects.document_id import DocumentId
from modules.documents.domain.value_objects.document_status import DocumentStatus
from modules.documents.infrastructure.persistence.models import DocumentRecordRow, DocumentVersionRow
from shared.infrastructure.database.db_models import get_session


def _version_from_row(r: DocumentVersionRow) -> DocumentVersion:
    return DocumentVersion(number=r.number, content_hash=DocumentHash(r.content_hash),
                           size_bytes=r.size_bytes, filename=r.filename, storage_key=r.storage_key,
                           note=r.note, created_at=r.created_at)


def _build(row: DocumentRecordRow, version_rows: list[DocumentVersionRow]) -> Document:
    versions = [_version_from_row(v) for v in sorted(version_rows, key=lambda v: v.number)]
    return Document(id=DocumentId(row.id), name=row.name, filename=row.filename,
                    status=DocumentStatus(row.status), versions=versions, created_at=row.created_at,
                    updated_at=row.updated_at, deleted_at=row.deleted_at)


def _load_many(session, rows: list[DocumentRecordRow]) -> list[Document]:
    if not rows:
        return []
    version_rows = session.exec(select(DocumentVersionRow).where(
        col(DocumentVersionRow.document_id).in_([r.id for r in rows])))
    by_doc: dict[str, list[DocumentVersionRow]] = {}
    for v in version_rows:
        by_doc.setdefault(v.document_id, []).append(v)
    return [_build(r, by_doc.get(r.id, [])) for r in rows]


class SqlDocumentRepository(DocumentRepository):
    """SQLModel implementation of the DocumentRepository port."""

    def save(self, document: Document) -> None:
        doc_id = str(document.id)
        with get_session() as session:
            session.merge(DocumentRecordRow(
                id=doc_id, name=document.name, filename=document.filename, status=document.status.value,
                created_at=document.created_at, updated_at=document.updated_at,
                deleted_at=document.deleted_at))
            existing = {r.number for r in session.exec(
                select(DocumentVersionRow).where(DocumentVersionRow.document_id == doc_id))}
            for v in document.versions:
                if v.number not in existing:
                    session.add(DocumentVersionRow(
                        document_id=doc_id, number=v.number, content_hash=v.content_hash.value,
                        size_bytes=v.size_bytes, filename=v.filename, storage_key=v.storage_key,
                        note=v.note, created_at=v.created_at))
            session.commit()

    def get(self, document_id: str) -> Document | None:
        with get_session() as session:
            row = session.get(DocumentRecordRow, document_id)
            return _load_many(session, [row])[0] if row else None

    def list(self, include_deleted: bool = False) -> list[Document]:
        stmt = select(DocumentRecordRow).order_by(DocumentRecordRow.created_at.desc())
        if not include_deleted:
            stmt = stmt.where(DocumentRecordRow.status == DocumentStatus.ACTIVE.value)
        with get_session() as session:
            return _load_many(session, list(session.exec(stmt)))

    def find_by_content_hash(self, content_hash: str, include_deleted: bool = False) -> list[Document]:
        with get_session() as session:
            ids = set(session.exec(select(DocumentVersionRow.document_id).where(
                DocumentVersionRow.content_hash == content_hash)))
            if not ids:
                return []
            stmt = select(DocumentRecordRow).where(col(DocumentRecordRow.id).in_(ids)).order_by(
                DocumentRecordRow.created_at.desc())
            if not include_deleted:
                stmt = stmt.where(DocumentRecordRow.status == DocumentStatus.ACTIVE.value)
            return _load_many(session, list(session.exec(stmt)))
