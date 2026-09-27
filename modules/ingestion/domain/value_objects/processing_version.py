from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProcessingVersion:
    """Identifies which parser+chunker (and their params) produced a given
    CanonicalDocument, so reprocessing with a different strategy or changed
    params can be detected and diffed against a prior version.

    Distinct from strategies.domain.value_objects.strategy_version, which
    versions a saved/named strategy config rather than stamping a specific
    ingestion output.
    """

    parser_name: str
    parser_params_hash: str
    chunker_name: str
    chunker_params_hash: str
    revision: int = 1

    @property
    def key(self) -> str:
        return (f"{self.parser_name}:{self.parser_params_hash}|"
                f"{self.chunker_name}:{self.chunker_params_hash}|r{self.revision}")

    def bumped(self) -> ProcessingVersion:
        return ProcessingVersion(self.parser_name, self.parser_params_hash,
                                  self.chunker_name, self.chunker_params_hash,
                                  self.revision + 1)

    def matches_strategy(self, parser_name: str, parser_params_hash: str,
                          chunker_name: str, chunker_params_hash: str) -> bool:
        """True if this version was produced by the given parser/chunker+params,
        ignoring revision — use to detect whether reprocessing is needed."""
        return (self.parser_name == parser_name and self.parser_params_hash == parser_params_hash
                and self.chunker_name == chunker_name and self.chunker_params_hash == chunker_params_hash)
