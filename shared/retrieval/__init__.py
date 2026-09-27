"""
NOTE (architecture decision, flag for review): the target folder-structure doc
doesn't define a home for the actual RAG retrieval pipeline engine (only for
strategy *config* under modules/strategies/domain/models/retrieval_config.py
and orchestration under modules/experiments/). Since section 7 of the doc says
these are "capabilities used by the Experiment Engine" rather than a primary
business module, this pipeline engine (moved as-is from rag_os.retrieval) is
placed here under shared/retrieval/ as a cross-cutting capability, parallel to
shared/ai/. Revisit if you'd rather nest it under modules/experiments/infrastructure/.
"""
from shared.retrieval import legacy_faiss_local, legacy_hybrid_bm25_vector, legacy_qdrant_cloud  # noqa: F401
from shared.retrieval.legacy_base import Retriever, retriever_registry
from shared.retrieval.pipeline_context import Candidate, PipelineContext
from shared.retrieval.pipeline_runner import PipelineStepConfig, run_pipeline
from shared.retrieval.pipeline_step import PipelineStep, pipeline_step_registry

__all__ = ["Retriever", "retriever_registry", "Candidate", "PipelineContext", "PipelineStep",
           "pipeline_step_registry", "PipelineStepConfig", "run_pipeline"]
