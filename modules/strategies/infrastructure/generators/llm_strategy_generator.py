from __future__ import annotations


class LlmStrategyGenerator:
    """Stub. Implements CandidateGenerator (duck-typed) once an LLM client is wired in."""

    def __init__(self, llm=None):
        self.llm = llm

    def generate(self, count: int = 3):
        raise NotImplementedError("LLM strategy generation is not implemented yet.")