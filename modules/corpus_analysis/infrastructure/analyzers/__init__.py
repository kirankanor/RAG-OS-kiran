from modules.corpus_analysis.infrastructure.analyzers import (
    duplicate_analyzer, language_analyzer, ocr_analyzer, size_analyzer, structure_analyzer, table_analyzer,
)
from modules.corpus_analysis.infrastructure.analyzers.base import Analyzer, analyzer_registry

__all__ = ["Analyzer", "analyzer_registry"]
