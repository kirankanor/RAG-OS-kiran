from __future__ import annotations

import re

from modules.corpus_analysis.domain.models.structure_profile import StructureProfile
from modules.corpus_analysis.infrastructure.analyzers.base import Analyzer, analyzer_registry
from modules.corpus_analysis.infrastructure.analyzers.text_utils import split_paragraphs

_MD_HEADING_RE = re.compile(r"^#{1,6}\s+\S")
_NUMBERED_HEADING_RE = re.compile(r"^\d+(?:\.\d+)+\.?\s+\S")
_KEYWORD_HEADING_RE = re.compile(r"^(?:chapter|section|article|part)\s+[\w.]+", re.IGNORECASE)
_LIST_RE = re.compile(r"^\s*(?:[-*\u2022]|\d+[.)])\s+\S")
_CODE_RE = re.compile(
    r"^\s*(?:def |class |import |from \S+ import |function |const |let |var |public |private |static |#include|@\w+)")


def _is_heading(line: str) -> bool:
    s = line.strip()
    if not s or len(s) > 100:
        return False
    if _MD_HEADING_RE.match(s) or _NUMBERED_HEADING_RE.match(s):
        return True
    if _KEYWORD_HEADING_RE.match(s) and len(s.split()) <= 10 and not s.endswith("."):
        return True
    letters = [c for c in s if c.isalpha()]
    return len(letters) >= 3 and s.isupper() and len(s.split()) <= 10 and not s.endswith((".", ","))


@analyzer_registry.register("structure", "Paragraphs, headings, list items and code lines.")
class StructureAnalyzer(Analyzer):
    name = "structure"
    produces = "structure"

    def analyze(self, documents):
        docs = list(documents)
        if not docs:
            return StructureProfile()
        num_paragraphs = para_chars = 0
        num_headings = docs_with_headings = list_items = code_lines = non_empty = 0
        for d in docs:
            paragraphs = split_paragraphs(d.text)
            num_paragraphs += len(paragraphs)
            para_chars += sum(len(p) for p in paragraphs)
            in_fence, prev_code, doc_headings = False, False, 0
            for line in d.text.splitlines():
                s = line.strip()
                if s.startswith("```"):
                    in_fence = not in_fence
                    continue
                if not s:
                    prev_code = False if not in_fence else prev_code
                    continue
                non_empty += 1
                indented = line.startswith(("    ", "\t"))
                if in_fence or _CODE_RE.match(line) or s.endswith((";", "{", "}")) or (indented and prev_code):
                    code_lines += 1
                    prev_code = True
                    continue
                prev_code = False
                if _is_heading(line):
                    doc_headings += 1
                elif _LIST_RE.match(line):
                    list_items += 1
            num_headings += doc_headings
            docs_with_headings += 1 if doc_headings else 0
        return StructureProfile(
            num_paragraphs=num_paragraphs,
            avg_paragraph_chars=round(para_chars / num_paragraphs, 1) if num_paragraphs else 0.0,
            num_headings=num_headings, docs_with_headings=docs_with_headings,
            heading_doc_ratio=round(docs_with_headings / len(docs), 3),
            num_list_items=list_items, num_code_lines=code_lines,
            code_line_ratio=round(code_lines / non_empty, 3) if non_empty else 0.0,
        )
