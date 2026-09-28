from __future__ import annotations

from enum import Enum


class MetricName(str, Enum):
    RECALL = "recall"
    PRECISION = "precision"
    MRR = "mrr"
    NDCG = "ndcg"

    def label(self, k: int) -> str:
        """Stored metric name, e.g. 'recall@5'. MRR has no k in its label."""
        return self.value if self is MetricName.MRR else f"{self.value}@{k}"
