from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from modules.decisions.domain.rules.scoring import clamp
from modules.strategies.domain.entities.strategy import Strategy

# Mix of evaluation metrics that forms the quality value. Precision is left out on
# purpose: relevance is snippet-based, so precision mostly rewards small chunks.
QUALITY_METRIC_WEIGHTS: dict[str, float] = {"recall": 0.4, "mrr": 0.3, "ndcg": 0.3}

_ENGLISH_ONLY_EMBEDDERS = {"local_minilm", "cohere_embed_v3"}
_MULTILINGUAL_EMBEDDERS = {"openai_text_embedding_3_small"}
_FIT_STEP = 0.25


def quality_value(metrics: Mapping[str, float]) -> tuple[float, str]:
    """Weighted mean of recall/mrr/ndcg (whichever the evaluation produced, e.g. 'recall@3')."""
    parts: list[tuple[str, float, float]] = []
    for kind, weight in QUALITY_METRIC_WEIGHTS.items():
        for name, value in metrics.items():
            if name == kind or name.startswith(kind + "@"):
                parts.append((name, weight, float(value)))
                break
    if not parts:
        return 0.0, "no recall/mrr/ndcg metrics available"
    total_weight = sum(w for _, w, _ in parts)
    value = sum(w * v for _, w, v in parts) / total_weight
    return clamp(value), ", ".join(f"{n}={v:.3f}" for n, _, v in parts)


@dataclass(frozen=True)
class FitResult:
    score: float
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def corpus_fit(strategy: Strategy, features: Mapping[str, Any]) -> FitResult:
    """How well the strategy's components suit the corpus (see CorpusProfile.features()).
    Starts neutral at 0.5; each matching rule moves it by 0.25."""
    score = 0.5
    notes: list[str] = []
    warnings: list[str] = []
    chunker, embedder = strategy.chunker.name, strategy.embedder.name

    if features.get("structure_level") == "structured" and chunker == "markdown_aware":
        score += _FIT_STEP
        notes.append("markdown_aware chunking matches a heading-rich corpus")

    if float(features.get("code_line_ratio", 0.0)) >= 0.3:
        if chunker == "code_aware":
            score += _FIT_STEP
            notes.append("code_aware chunking matches a code-heavy corpus")
        elif chunker in ("fixed_size", "sentence_window"):
            score -= _FIT_STEP
            warnings.append(f"{chunker} chunking can split code mid-function")

    language = features.get("primary_language", "unknown")
    non_english = bool(features.get("is_multilingual")) or language not in ("en", "unknown")
    if non_english:
        multilingual_params = "multilingual" in str(strategy.embedder.params).lower()
        if embedder in _MULTILINGUAL_EMBEDDERS or multilingual_params:
            score += _FIT_STEP
            notes.append("embedding model handles non-English text")
        elif embedder in _ENGLISH_ONLY_EMBEDDERS:
            score -= _FIT_STEP
            warnings.append(f"{embedder} is English-focused but the corpus is non-English/multilingual "
                            f"(primary language: {language})")
    return FitResult(clamp(score), notes, warnings)


def corpus_warnings(features: Mapping[str, Any]) -> list[str]:
    """Corpus-level issues that no strategy in the comparison fixes on its own."""
    out: list[str] = []
    if features.get("ocr_recommended"):
        pct = float(features.get("scanned_doc_ratio", 0.0)) * 100
        out.append(f"About {pct:.0f}% of documents look scanned; the parsers do not OCR, "
                   "so their text will be missing from every strategy's index.")
    if float(features.get("duplicate_doc_ratio", 0.0)) >= 0.2:
        pct = float(features["duplicate_doc_ratio"]) * 100
        out.append(f"{pct:.0f}% of documents are exact duplicates; deduplicate before indexing "
                   "or retrieval results will repeat.")
    return out
