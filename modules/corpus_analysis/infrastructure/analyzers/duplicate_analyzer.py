from __future__ import annotations

import hashlib
import heapq

from modules.corpus_analysis.domain.models.content_profile import DuplicateStats
from modules.corpus_analysis.infrastructure.analyzers.base import Analyzer, analyzer_registry
from modules.corpus_analysis.infrastructure.analyzers.text_utils import normalize, split_paragraphs

_SHINGLE_WORDS = 5
_SKETCH_SIZE = 128
_MIN_PARAGRAPH_CHARS = 40


def _hash(s: str) -> int:
    return int.from_bytes(hashlib.blake2b(s.encode(), digest_size=8).digest(), "big")


def _sketch(normalized: str) -> frozenset[int]:
    """Bottom-k MinHash sketch of the document's word shingles."""
    words = normalized.split()
    if len(words) <= _SHINGLE_WORDS:
        shingles = {" ".join(words)}
    else:
        shingles = {" ".join(words[i:i + _SHINGLE_WORDS]) for i in range(len(words) - _SHINGLE_WORDS + 1)}
    return frozenset(heapq.nsmallest(_SKETCH_SIZE, {_hash(s) for s in shingles}))


def _jaccard(a: frozenset[int], b: frozenset[int]) -> float:
    union_k = heapq.nsmallest(_SKETCH_SIZE, a | b)
    if not union_k:
        return 0.0
    return sum(1 for h in union_k if h in a and h in b) / len(union_k)


@analyzer_registry.register("duplicates", "Exact and near-duplicate documents, plus repeated paragraphs.")
class DuplicateAnalyzer(Analyzer):
    """Near-duplicate detection is pairwise, so it only looks at the first
    `max_near_docs` distinct documents."""

    name = "duplicates"
    produces = "duplicates"

    def __init__(self, near_threshold: float = 0.85, max_near_docs: int = 300):
        self.near_threshold = near_threshold
        self.max_near_docs = max_near_docs

    def analyze(self, documents):
        docs = [d for d in documents if d.text.strip()]
        if not docs:
            return DuplicateStats()
        seen: set[str] = set()
        unique, exact = [], 0
        for d in docs:
            key = hashlib.sha256(normalize(d.text).encode()).hexdigest()
            if key in seen:
                exact += 1
            else:
                seen.add(key)
                unique.append(d)
        sketches = [_sketch(normalize(d.text)) for d in unique[:self.max_near_docs]]
        near = sum(1 for i in range(len(sketches)) for j in range(i + 1, len(sketches))
                   if _jaccard(sketches[i], sketches[j]) >= self.near_threshold)
        paragraphs = [normalize(p) for d in docs for p in split_paragraphs(d.text)
                      if len(p) >= _MIN_PARAGRAPH_CHARS]
        para_ratio = (len(paragraphs) - len(set(paragraphs))) / len(paragraphs) if paragraphs else 0.0
        return DuplicateStats(exact_duplicate_docs=exact, near_duplicate_pairs=near,
                              duplicate_doc_ratio=round(exact / len(docs), 3),
                              duplicate_paragraph_ratio=round(para_ratio, 3))
