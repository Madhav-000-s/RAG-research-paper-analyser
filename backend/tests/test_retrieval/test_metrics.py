"""Tests for evaluation metrics (imported from evaluation module)."""

import sys
from pathlib import Path

import pytest

# Add evaluation dir to path so we can import metrics
sys.path.insert(0, str(Path(__file__).parents[3] / "evaluation"))

from metrics import (
    EvalSample,
    citation_precision,
    citation_recall,
    compute_all_metrics,
    retrieval_recall_at_k,
)


def _make_sample(
    retrieved: list[int],
    cited: list[int],
    ground_truth: list[int],
) -> EvalSample:
    return EvalSample(
        question="test",
        answer="test [1]",
        retrieved_chunk_indices=retrieved,
        cited_chunk_indices=cited,
        ground_truth_answer="ground truth",
        ground_truth_chunk_indices=ground_truth,
    )


class TestRetrievalRecall:
    def test_perfect_recall(self):
        sample = _make_sample([0, 1, 2, 3, 4], [], [0, 1, 2])
        assert retrieval_recall_at_k([sample], k=5) == 1.0

    def test_partial_recall(self):
        sample = _make_sample([0, 1, 5, 6, 7], [], [0, 1, 2, 3])
        # 2 out of 4 ground truth found in top 5
        assert retrieval_recall_at_k([sample], k=5) == 0.5

    def test_zero_recall(self):
        sample = _make_sample([10, 11, 12, 13, 14], [], [0, 1, 2])
        assert retrieval_recall_at_k([sample], k=5) == 0.0

    def test_k_limits_retrieved(self):
        # Ground truth chunk at index 5 is only at position 6 (0-indexed)
        sample = _make_sample([0, 1, 2, 3, 4, 5], [], [5])
        assert retrieval_recall_at_k([sample], k=5) == 0.0
        assert retrieval_recall_at_k([sample], k=6) == 1.0

    def test_empty_samples(self):
        assert retrieval_recall_at_k([], k=5) == 0.0


class TestCitationPrecision:
    def test_perfect_precision(self):
        sample = _make_sample([], [0, 1, 2], [0, 1, 2, 3])
        assert citation_precision([sample]) == 1.0

    def test_half_precision(self):
        sample = _make_sample([], [0, 1, 5, 6], [0, 1])
        assert citation_precision([sample]) == 0.5

    def test_zero_precision(self):
        sample = _make_sample([], [10, 11], [0, 1, 2])
        assert citation_precision([sample]) == 0.0

    def test_no_citations(self):
        sample = _make_sample([], [], [0, 1])
        assert citation_precision([sample]) == 0.0


class TestCitationRecall:
    def test_perfect_recall(self):
        sample = _make_sample([], [0, 1, 2], [0, 1, 2])
        assert citation_recall([sample]) == 1.0

    def test_partial_recall(self):
        sample = _make_sample([], [0], [0, 1, 2])
        assert abs(citation_recall([sample]) - 1 / 3) < 1e-10

    def test_zero_recall(self):
        sample = _make_sample([], [10], [0, 1, 2])
        assert citation_recall([sample]) == 0.0


class TestComputeAllMetrics:
    def test_returns_all_keys(self):
        sample = _make_sample([0, 1, 2, 3, 4], [0, 1], [0, 1, 2])
        result = compute_all_metrics([sample])
        assert "retrieval_recall@5" in result
        assert "retrieval_recall@10" in result
        assert "citation_precision" in result
        assert "citation_recall" in result
        assert "num_samples" in result
        assert result["num_samples"] == 1
