from __future__ import annotations

import re
from collections import Counter

from modules.corpus_analysis.domain.models.language_profile import LanguageProfile
from modules.corpus_analysis.infrastructure.analyzers.base import Analyzer, analyzer_registry

_SAMPLE_CHARS = 50_000
_MIN_STOPWORD_HITS = 3
_WORD_RE = re.compile(r"[^\W\d_]+")

_SCRIPT_RANGES = (
    ("gujarati", 0x0A80, 0x0AFF), ("devanagari", 0x0900, 0x097F), ("arabic", 0x0600, 0x06FF),
    ("cyrillic", 0x0400, 0x04FF), ("kana", 0x3040, 0x30FF), ("hangul", 0xAC00, 0xD7AF),
    ("han", 0x4E00, 0x9FFF),
)
_SCRIPT_LANG = {"gujarati": "gu", "devanagari": "hi", "arabic": "ar", "cyrillic": "ru",
                "kana": "ja", "hangul": "ko", "han": "zh"}

_STOPWORDS: dict[str, frozenset[str]] = {
    "en": frozenset("the and of to in is that it for with as was on are this be by at not".split()),
    "es": frozenset("el la de que y en los del se las por un para con no una su al es lo como m\u00e1s".split()),
    "fr": frozenset("le la les des du de et en un une que est pour pas qui dans sur au avec ce il".split()),
    "de": frozenset("der die und das den von zu mit sich des auf f\u00fcr ist im dem nicht ein eine als auch".split()),
    "pt": frozenset("de do da em um uma que para com n\u00e3o por mais se dos das ao \u00e9 os as".split()),
    "it": frozenset("il lo la gli le di del della che \u00e8 per un una in con non sono si dei al come".split()),
    "nl": frozenset("de het een van en in is dat op te zijn met voor niet aan er ook als bij".split()),
}


def _script_of(ch: str) -> str:
    o = ord(ch)
    for name, lo, hi in _SCRIPT_RANGES:
        if lo <= o <= hi:
            return name
    return "latin" if o <= 0x024F or 0x1E00 <= o <= 0x1EFF else "other"


def detect_script(text: str) -> str:
    counts = Counter(_script_of(c) for c in text if c.isalpha())
    if not counts:
        return "unknown"
    if counts.get("kana") and "han" in counts:  # Japanese mixes kana and han
        return "kana"
    return counts.most_common(1)[0][0]


def detect_language(text: str, script: str) -> str:
    if script == "unknown":
        return "unknown"
    if script != "latin":
        return _SCRIPT_LANG.get(script, "unknown")
    tokens = _WORD_RE.findall(text.lower())
    scores = {lang: sum(1 for t in tokens if t in words) for lang, words in _STOPWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] >= _MIN_STOPWORD_HITS else "unknown"


@analyzer_registry.register("language", "Per-document script and language guess (stopwords / Unicode script).")
class LanguageAnalyzer(Analyzer):
    name = "language"
    produces = "language"

    def analyze(self, documents):
        docs = list(documents)
        if not docs:
            return LanguageProfile()
        languages: Counter[str] = Counter()
        scripts: Counter[str] = Counter()
        for d in docs:
            sample = d.text[:_SAMPLE_CHARS]
            script = detect_script(sample)
            scripts[script] += 1
            languages[detect_language(sample, script)] += 1
        known = {k: v for k, v in languages.items() if k != "unknown"}
        primary = max(known, key=known.get) if known else "unknown"
        return LanguageProfile(
            primary_language=primary, confidence=round(languages[primary] / len(docs), 3),
            language_counts=dict(languages.most_common()), script_counts=dict(scripts.most_common()))
