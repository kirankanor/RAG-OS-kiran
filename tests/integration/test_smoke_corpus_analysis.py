import pytest

from modules.corpus_analysis.application.commands.analyze_corpus import AnalyzeCorpusCommand
from modules.corpus_analysis.application.queries.get_corpus_profile import GetCorpusProfileQuery
from modules.corpus_analysis.application.services.corpus_analysis_service import CorpusAnalysisService
from modules.corpus_analysis.domain.entities.analysis_run import AnalysisStatus
from modules.corpus_analysis.domain.exceptions import (
    AnalysisRunNotFoundError, InvalidCorpusError, ProfileNotFoundError,
)
from shared.domain.types import Document

PROSE = "The quick brown fox jumps over the lazy dog and the cat sat on the mat. " * 5
MARKDOWN = """# Title

The cat sat on the mat and the dog was in the house with a bone.

## Section

- item one
- item two

| a | b |
| 1 | 2 |
"""
CODE = "def add(a, b):\n    return a + b\n\nclass Foo:\n    pass\n"


def _write(env, name, text):
    p = env / name
    p.write_text(text, encoding="utf-8")
    return str(p)


def test_analyze_files_end_to_end(isolated_env):
    files = [_write(isolated_env, "a.md", MARKDOWN), _write(isolated_env, "b.txt", PROSE),
             _write(isolated_env, "c.txt", PROSE)]  # c is an exact copy of b
    profile = AnalyzeCorpusCommand().execute(files, name="demo")

    assert profile.statistics.num_documents == 3
    assert profile.statistics.total_chars == len(MARKDOWN) + 2 * len(PROSE)
    assert profile.structure.num_headings == 2 and profile.structure.docs_with_headings == 1
    assert profile.structure.num_list_items == 2
    assert profile.structure.structure_level == "semi"
    assert profile.content.tables.num_tables == 1 and profile.content.tables.docs_with_tables == 1
    assert profile.content.duplicates.exact_duplicate_docs == 1
    assert profile.language.primary_language == "en" and not profile.language.is_multilingual
    assert profile.content.ocr.ocr_recommended is False
    assert profile.features()["num_documents"] == 3

    q = GetCorpusProfileQuery()
    assert q.execute(profile.id).to_dict() == profile.to_dict()       # survives the DB round trip
    assert q.for_run(profile.analysis_run_id).id == profile.id
    assert [p.id for p in q.list()] == [profile.id]
    run = CorpusAnalysisService().get_run(profile.analysis_run_id)
    assert run.status == AnalysisStatus.COMPLETED and run.name == "demo"
    assert run.source_filenames == ["a.md", "b.txt", "c.txt"]


def test_code_and_scanned_pdf_and_gujarati(isolated_env):
    docs = [
        Document(source_filename="x.py", text=CODE),
        Document(source_filename="scan.pdf", text="", metadata={"num_pages": 10}),
        Document(source_filename="real.pdf", text="word " * 1000, metadata={"num_pages": 2}),
        Document(source_filename="gu.txt", text="\u0a97\u0ac1\u0a9c\u0ab0\u0abe\u0aa4\u0ac0 " * 20),
    ]
    p = CorpusAnalysisService().analyze_documents(docs)
    assert p.structure.num_code_lines == 4
    assert p.content.ocr.likely_scanned_files == ["scan.pdf"] and p.content.ocr.ocr_recommended
    assert p.statistics.total_pages == 12 and p.statistics.empty_documents == 1
    assert p.language.script_counts.get("gujarati") == 1
    assert p.language.language_counts.get("gu") == 1


def test_near_duplicates(isolated_env):
    base = [f"word{i}" for i in range(200)]
    near = list(base)
    near[100] = "changed"
    other = [f"other{i}" for i in range(200)]
    docs = [Document(source_filename=n, text=" ".join(w)) for n, w in
            (("a.txt", base), ("b.txt", near), ("c.txt", other))]
    p = CorpusAnalysisService().analyze_documents(docs, analyzers=["duplicates"])
    assert p.content.duplicates.near_duplicate_pairs == 1
    assert p.content.duplicates.exact_duplicate_docs == 0


def test_analyzer_subset_leaves_other_sections_empty(isolated_env):
    p = CorpusAnalysisService().analyze_documents([Document(source_filename="a.txt", text=PROSE)],
                                                  analyzers=["size"])
    assert p.statistics.num_documents == 1
    assert p.language.primary_language == "unknown" and p.structure.num_paragraphs == 0


def test_invalid_inputs(isolated_env):
    svc = CorpusAnalysisService()
    with pytest.raises(InvalidCorpusError):
        svc.analyze_files([])
    with pytest.raises(InvalidCorpusError):
        svc.analyze_files([str(isolated_env / "nope.txt")])
    with pytest.raises(InvalidCorpusError):
        svc.analyze_documents([Document(source_filename="a.txt", text="hi")], analyzers=["nope"])
    with pytest.raises(InvalidCorpusError):
        svc.analyze_documents([])
    bad = _write(isolated_env, "weird.xyz", "data")           # no parser for .xyz
    with pytest.raises(InvalidCorpusError):
        svc.analyze_files([bad])
    good = _write(isolated_env, "ok.txt", PROSE)
    p = svc.analyze_files([bad, good])                          # skipped with a warning
    assert p.statistics.num_documents == 1 and len(p.warnings) == 1 and "weird.xyz" in p.warnings[0]
    with pytest.raises(ProfileNotFoundError):
        svc.get_profile("nope")
    with pytest.raises(AnalysisRunNotFoundError):
        svc.get_profile_for_run("nope")
