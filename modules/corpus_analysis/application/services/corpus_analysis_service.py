from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path

from sqlmodel import SQLModel

from modules.corpus_analysis.domain.entities.analysis_run import AnalysisRun
from modules.corpus_analysis.domain.entities.corpus_profile import CorpusProfile
from modules.corpus_analysis.domain.exceptions import (
    AnalysisRunNotFoundError, CorpusAnalysisError, InvalidCorpusError, ProfileNotFoundError,
)
from modules.corpus_analysis.domain.models.content_profile import ContentProfile
# Importing the package registers all analyzers.
from modules.corpus_analysis.infrastructure.analyzers import analyzer_registry
# Importing models registers the corpus_analysis tables on SQLModel.metadata.
from modules.corpus_analysis.infrastructure.persistence import models as _models  # noqa: F401
from modules.corpus_analysis.infrastructure.persistence.repository import CorpusAnalysisRepository
from modules.ingestion.infrastructure.parsers import parser_for_file
from shared.domain.types import Document
from shared.infrastructure.database.db_models import get_engine

DEFAULT_ANALYZERS: tuple[str, ...] = ("size", "structure", "language", "duplicates", "tables", "ocr")


def _ensure_tables() -> None:
    SQLModel.metadata.create_all(get_engine())  # idempotent


class CorpusAnalysisService:
    def __init__(self, repository: CorpusAnalysisRepository | None = None):
        _ensure_tables()
        self.repository = repository or CorpusAnalysisRepository()

    def analyze_files(self, file_paths: Sequence[str], name: str = "",
                      analyzers: Sequence[str] | None = None) -> CorpusProfile:
        """Parse each file with its default parser, then analyze the parsed documents.
        Missing files reject the whole request; files that fail to parse are skipped
        and reported in profile.warnings."""
        if not file_paths:
            raise InvalidCorpusError("No file paths provided.", ["No file paths provided."])
        missing = [f"File not found: {fp}" for fp in file_paths if not Path(fp).is_file()]
        if missing:
            raise InvalidCorpusError("Invalid corpus: " + "; ".join(missing), missing)
        documents: list[Document] = []
        warnings: list[str] = []
        for fp in file_paths:
            try:
                documents.append(parser_for_file(fp).parse(fp))
            except Exception as e:  # noqa: BLE001 - one bad file must not sink the corpus
                warnings.append(f"Could not parse {Path(fp).name}: {e}")
        if not documents:
            raise InvalidCorpusError("No documents could be parsed: " + "; ".join(warnings), warnings)
        return self.analyze_documents(documents, name=name, warnings=warnings, analyzers=analyzers)

    def analyze_documents(self, documents: Iterable[Document], name: str = "",
                          warnings: Sequence[str] | None = None,
                          analyzers: Sequence[str] | None = None) -> CorpusProfile:
        docs = list(documents)
        if not docs:
            raise InvalidCorpusError("No documents to analyze.", ["No documents to analyze."])
        selected = list(analyzers) if analyzers is not None else list(DEFAULT_ANALYZERS)
        unknown = [a for a in selected if a not in analyzer_registry.names()]
        if unknown:
            raise InvalidCorpusError(f"Unknown analyzers {unknown}. Available: {analyzer_registry.names()}",
                                     [f"Unknown analyzer '{a}'." for a in unknown])

        run = AnalysisRun(name=name, source_filenames=[d.source_filename for d in docs])
        run.start()
        self.repository.save_run(run)
        try:
            results = {}
            for analyzer_name in selected:
                analyzer = analyzer_registry.create(analyzer_name)
                results[analyzer.produces] = analyzer.analyze(docs)
        except Exception as e:  # noqa: BLE001
            run.fail(f"{type(e).__name__}: {e}")
            self.repository.save_run(run)
            raise CorpusAnalysisError(f"Analysis failed: {e}") from e

        defaults = CorpusProfile()
        profile = CorpusProfile(
            analysis_run_id=run.id,
            statistics=results.get("statistics", defaults.statistics),
            structure=results.get("structure", defaults.structure),
            language=results.get("language", defaults.language),
            content=ContentProfile(tables=results.get("tables", defaults.content.tables),
                                   duplicates=results.get("duplicates", defaults.content.duplicates),
                                   ocr=results.get("ocr", defaults.content.ocr)),
            warnings=list(warnings or []))
        self.repository.save_profile(profile)
        run.complete()
        self.repository.save_run(run)
        return profile

    def get_profile(self, profile_id: str) -> CorpusProfile:
        p = self.repository.get_profile(profile_id)
        if p is None:
            raise ProfileNotFoundError(f"No corpus profile with id '{profile_id}'")
        return p

    def get_profile_for_run(self, run_id: str) -> CorpusProfile:
        if self.repository.get_run(run_id) is None:
            raise AnalysisRunNotFoundError(f"No analysis run with id '{run_id}'")
        p = self.repository.get_profile_for_run(run_id)
        if p is None:
            raise ProfileNotFoundError(f"Analysis run '{run_id}' has no profile (it may have failed).")
        return p

    def get_run(self, run_id: str) -> AnalysisRun:
        r = self.repository.get_run(run_id)
        if r is None:
            raise AnalysisRunNotFoundError(f"No analysis run with id '{run_id}'")
        return r

    def list_profiles(self) -> list[CorpusProfile]:
        return self.repository.list_profiles()
