import zipfile

import pytest

from modules.artifacts.application.commands.generate_code import GenerateCodeCommand
from modules.artifacts.application.commands.generate_report import GenerateReportCommand
from modules.artifacts.application.commands.package_project import PackageProjectCommand
from modules.artifacts.application.queries.list_artifacts import ListArtifactsQuery
from modules.artifacts.application.services.report_service import ReportService
from modules.artifacts.domain.exceptions import ArtifactNotFoundError, InvalidArtifactError
from modules.artifacts.domain.value_objects.artifact_status import ArtifactStatus
from modules.artifacts.domain.value_objects.artifact_type import ArtifactType
from modules.decisions.domain.exceptions import DecisionNotFoundError
from modules.documents.application.services.document_service import DocumentService
from modules.experiments.application.services.experiment_service import ExperimentService
from modules.projects.application.commands.create_project import CreateProjectCommand
from modules.strategies.domain.exceptions import StrategyNotFoundError
from modules.users.application.services.user_service import UserService
from tests.integration.test_smoke_experiments import _config, _strategy  # also registers test doubles
from tests.unit.decisions.test_decision_engine import _decision


def test_report_code_and_listing(isolated_env):
    reports = ReportService()
    d = _decision()
    reports.decisions.repository.save(d)

    art = GenerateReportCommand(reports).execute(d.id)
    q = ListArtifactsQuery()
    assert art.status == ArtifactStatus.COMPLETED and art.type == ArtifactType.REPORT
    assert "# Strategy recommendation" in q.file_path(art.id).read_text(encoding="utf-8")
    assert q.get(art.id).size_bytes == art.size_bytes and len(art.content_hash) == 64

    s = _strategy("s1")
    code = GenerateCodeCommand().execute(str(s.id))
    compile(q.file_path(code.id).read_text(encoding="utf-8"), "generated.py", "exec")
    assert [a.id for a in q.execute(source_type="strategy")] == [code.id]
    assert [a.id for a in q.execute(artifact_type=ArtifactType.REPORT)] == [art.id]
    assert len(q.execute()) == 2

    with pytest.raises(DecisionNotFoundError):
        GenerateReportCommand(reports).execute("nope")
    with pytest.raises(InvalidArtifactError):
        GenerateReportCommand(reports).execute(d.id, summarize_with="nope")
    with pytest.raises(StrategyNotFoundError):
        GenerateCodeCommand().execute("nope")
    with pytest.raises(ArtifactNotFoundError):
        q.get("nope")


def test_package_project(isolated_env):
    owner = UserService().register("owner@example.com", "password123")
    doc = DocumentService().upload("Cats", "cats.txt", b"Cats purr and sleep all day.")
    exp = ExperimentService().create("cmp", _config(isolated_env), [str(_strategy("s1").id)])
    d = _decision()
    d.experiment_id = str(exp.id)
    reports = ReportService()
    reports.decisions.repository.save(d)
    project = CreateProjectCommand().execute("My Project", str(owner.id), document_ids=[str(doc.id)],
                                             experiment_ids=[str(exp.id)])

    art = PackageProjectCommand().execute(project.id, include_documents=True)
    assert art.type == ArtifactType.PACKAGE and art.filename == "My-Project-package.zip"
    with zipfile.ZipFile(ListArtifactsQuery().file_path(art.id)) as zf:
        names = set(zf.namelist())
    assert {"project.json", "README.md", f"experiments/{exp.id}/experiment.json",
            f"reports/decision-{d.id}.md", f"documents/{doc.id}/cats.txt"} <= names
    assert any(n.startswith("code/") and n.endswith(".py") for n in names)

    slim = PackageProjectCommand().execute(project.id)
    with zipfile.ZipFile(ListArtifactsQuery().file_path(slim.id)) as zf:
        assert not any(n.startswith("documents/") for n in zf.namelist())
