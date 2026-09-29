import io
import zipfile

import pytest

from modules.artifacts.infrastructure.generators.code_generator import generate_strategy_script, slugify
from modules.artifacts.infrastructure.generators.markdown_generator import render_decision_report
from modules.artifacts.infrastructure.generators.zip_generator import build_zip
from modules.artifacts.infrastructure.llm.artifact_llm_generator import ArtifactLlmGenerator
from modules.strategies.domain.entities.strategy import Strategy
from modules.strategies.domain.models.chunker_config import ChunkerConfig
from modules.strategies.domain.models.embedding_config import EmbeddingConfig
from modules.strategies.domain.models.retrieval_config import RetrievalConfig
from tests.unit.decisions.test_decision_engine import _decision


def test_zip_is_deterministic_and_safe():
    files = {"a/b.txt": "x", "c.bin": b"y"}
    data = build_zip(files)
    assert data == build_zip(dict(reversed(list(files.items()))))
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        assert zf.namelist() == ["a/b.txt", "c.bin"] and zf.read("a/b.txt") == b"x"
    for bad in ("../x", "/abs", "a\\b", ""):
        with pytest.raises(ValueError):
            build_zip({bad: "x"})


def test_generated_script_compiles_and_carries_config():
    s = Strategy(name='My "strat"', chunker=ChunkerConfig("fixed_size", {"chunk_size": 500}),
                 embedder=EmbeddingConfig("local_minilm"), retrieval=RetrievalConfig("faiss_flat_l2", top_k=7))
    code = generate_strategy_script(s)
    compile(code, "generated.py", "exec")
    assert "'fixed_size'" in code and "'chunk_size': 500" in code and "DEFAULT_TOP_K = 7" in code
    assert "NOTE" not in code
    c = Strategy(name="c", chunker=ChunkerConfig("contextual"))
    compile(generate_strategy_script(c), "generated.py", "exec")
    assert "NOTE" in generate_strategy_script(c)
    assert slugify("a b/c") == "a-b-c" and slugify("///", "x") == "x"


def test_decision_report_markdown():
    md = render_decision_report(_decision(), summary=" short summary ")
    assert md.startswith("# Strategy recommendation") and "## Summary\n\nshort summary" in md
    assert "**cloud** v1" in md and "| Rank | Strategy |" in md and "## Weights" in md
    assert "careful" in md and md.endswith("\n")


def test_llm_summarizer_falls_back_to_empty():
    class Gen:
        def generate(self, query, results):
            return "  ok  "

    class Broken:
        def generate(self, query, results):
            raise RuntimeError("down")

    assert ArtifactLlmGenerator(Gen()).summarize("text") == "ok"
    assert ArtifactLlmGenerator(Broken()).summarize("text") == ""
