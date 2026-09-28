"""Ingestion-level access point for the parser registry.

The registry itself lives with the strategies in infrastructure/parsers/base.py;
importing from the package (not .base) ensures all parsers are registered.
"""
from modules.ingestion.infrastructure.parsers import (  # noqa: F401
    DEFAULT_STRATEGY_BY_EXTENSION, Parser, parser_for_file, parser_registry,
)

__all__ = ["Parser", "parser_registry", "parser_for_file", "DEFAULT_STRATEGY_BY_EXTENSION"]
