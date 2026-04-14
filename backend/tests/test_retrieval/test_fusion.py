"""Tests for Reciprocal Rank Fusion."""

import uuid

import pytest

from app.retrieval.dense import ScoredChunk
from app.retrieval.fusion import reciprocal_rank_fusion


def _make_chunk(index: int, score: float = 0.0) -> ScoredChunk:
    return ScoredChunk(
        id=uuid.uuid5(uuid.NAMESPACE_DNS, f"chunk-{index}"),
        chunk_index=index,
        content=f"Chunk {index} content",
        page_number=1,
        section_heading=None,
        score=score,
    )


class TestReciprocalRankFusion:
    def test_single_list(self):
        chunks = [_make_chunk(0, 0.9), _make_chunk(1, 0.8)]
        result = reciprocal_rank_fusion([chunks], k=60)
        assert len(result) == 2
        # First ranked chunk should have higher RRF score
        assert result[0].score > result[1].score

    def test_two_lists_with_overlap(self):
        list_a = [_make_chunk(0), _make_chunk(1), _make_chunk(2)]
        list_b = [_make_chunk(2), _make_chunk(0), _make_chunk(3)]

        result = reciprocal_rank_fusion([list_a, list_b], k=60)

        # Chunk 0 appears in both lists (rank 1 in A, rank 2 in B)
        # Chunk 2 appears in both lists (rank 3 in A, rank 1 in B)
        # Both should have higher scores than chunks appearing once
        ids = [str(r.id) for r in result]
        chunk_0_id = str(_make_chunk(0).id)
        chunk_2_id = str(_make_chunk(2).id)

        # Chunks appearing in both lists should be ranked higher
        score_map = {str(r.id): r.score for r in result}
        chunk_3_id = str(_make_chunk(3).id)

        assert score_map[chunk_0_id] > score_map[chunk_3_id]
        assert score_map[chunk_2_id] > score_map[chunk_3_id]

    def test_empty_lists(self):
        result = reciprocal_rank_fusion([[], []])
        assert result == []

    def test_no_lists(self):
        result = reciprocal_rank_fusion([])
        assert result == []

    def test_rrf_score_formula(self):
        """Verify RRF score matches the formula: 1/(k+rank)."""
        k = 60
        list_a = [_make_chunk(0)]
        result = reciprocal_rank_fusion([list_a], k=k)
        expected_score = 1.0 / (k + 1)  # rank=1
        assert abs(result[0].score - expected_score) < 1e-10

    def test_two_lists_rrf_score(self):
        """Verify combined RRF score for a chunk in both lists."""
        k = 60
        list_a = [_make_chunk(0)]  # rank 1
        list_b = [_make_chunk(0)]  # rank 1
        result = reciprocal_rank_fusion([list_a, list_b], k=k)
        expected_score = 2.0 / (k + 1)
        assert abs(result[0].score - expected_score) < 1e-10

    def test_preserves_all_unique_chunks(self):
        list_a = [_make_chunk(0), _make_chunk(1)]
        list_b = [_make_chunk(2), _make_chunk(3)]
        result = reciprocal_rank_fusion([list_a, list_b], k=60)
        assert len(result) == 4
