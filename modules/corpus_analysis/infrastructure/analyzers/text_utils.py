from __future__ import annotations

import re

_BLANK_SPLIT_RE = re.compile(r"\n\s*\n")
_WS_RE = re.compile(r"\s+")


def normalize(text: str) -> str:
    return _WS_RE.sub(" ", text).strip().casefold()


def split_paragraphs(text: str) -> list[str]:
    """Blank-line separated blocks. Parsers such as docx/html join with single
    newlines, so when there are no blank lines and the lines are long (paragraph-like)
    each line is treated as a paragraph instead."""
    blocks = [b.strip() for b in _BLANK_SPLIT_RE.split(text) if b.strip()]
    if len(blocks) <= 1:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if len(lines) > 1 and sum(len(ln) for ln in lines) / len(lines) >= 60:
            return lines
    return blocks
