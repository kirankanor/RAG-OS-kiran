"""Domain-level Parser contract. Concrete strategies live in
modules/ingestion/infrastructure/parsers/ (moved from rag_os.ingestion.parsing).
NOTE: this currently just re-exports the existing Parser ABC unchanged
(see infrastructure/parsers/base.py) — split further when you actually
introduce a persistence-agnostic domain layer."""
from modules.ingestion.infrastructure.parsers.base import Parser, parser_registry  # noqa: F401
