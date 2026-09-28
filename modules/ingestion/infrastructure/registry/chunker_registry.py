"""Ingestion-level access point for the chunker registry.

The registry itself lives with the strategies in infrastructure/chunkers/base.py;
importing from the package (not .base) ensures all chunkers are registered.
"""
from modules.ingestion.infrastructure.chunkers import Chunker, chunker_registry  # noqa: F401

__all__ = ["Chunker", "chunker_registry"]
