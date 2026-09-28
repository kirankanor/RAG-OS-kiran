import pytest

from modules.ingestion.application.commands.start_ingestion import StartIngestionCommand
from modules.ingestion.application.dto.ingestion_dto import StartIngestionDTO
from modules.ingestion.application.queries.get_ingestion_status import GetIngestionStatusQuery
from modules.users.application.services.user_service import UserService
from modules.users.domain.exceptions import (
    EmailAlreadyRegisteredError, InvalidCredentialsError, InvalidTokenError,
)


def test_user_register_auth_verify(isolated_env):
    svc = UserService()
    user = svc.register("a@example.com", "password123")
    token = svc.authenticate("a@example.com", "password123")
    assert svc.verify_token(token).id == user.id

    with pytest.raises(InvalidCredentialsError):
        svc.authenticate("a@example.com", "wrong-password")
    with pytest.raises(EmailAlreadyRegisteredError):
        svc.register("A@example.com", "password123")
    with pytest.raises(InvalidTokenError):
        svc.verify_token("not.a.token")


def test_organization_flow(isolated_env):
    svc = UserService()
    user = svc.register("owner@example.com", "password123")
    org = svc.create_organization("Acme", str(user.id))
    assert svc.get_user(str(user.id)).organization_id == org.id


def test_ingestion_happy_path(isolated_env):
    f = isolated_env / "sample.txt"
    f.write_text("Hello world. " * 100, encoding="utf-8")
    dto = StartIngestionDTO(file_paths=[str(f)], chunker_name="fixed_size",
                            chunker_params={"chunk_size": 200, "overlap": 20})
    outcome = StartIngestionCommand().execute(dto)

    assert outcome.run.status == "completed"
    assert len(outcome.documents) == 1
    assert len(outcome.chunks) > 1

    # persisted: run status readable, canonical doc stored
    status = GetIngestionStatusQuery().execute(outcome.run.id)
    assert status.completed_jobs == 1
    from modules.ingestion.domain.interfaces.storage import document_storage_registry
    assert document_storage_registry.create("sql").exists(outcome.documents[0].id)


def test_ingestion_missing_file_fails_cleanly(isolated_env):
    dto = StartIngestionDTO(file_paths=[str(isolated_env / "nope.txt")])
    outcome = StartIngestionCommand().execute(dto)
    assert outcome.run.status == "failed"
    assert outcome.run.jobs[0].error_message