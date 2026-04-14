"""Evaluation metrics for RAG system quality."""

from dataclasses import dataclass
from statistics import mean


@dataclass
class EvalSample:
    question: str
    answer: str
    retrieved_chunk_indices: list[int]
    cited_chunk_indices: list[int]
    ground_truth_answer: str
    ground_truth_chunk_indices: list[int]


def retrieval_recall_at_k(samples: list[EvalSample], k: int = 5) -> float:
    """
    What fraction of ground-truth chunks appear in the top-k retrieved chunks?
    Averaged across all samples.
    """
    recalls = []
    for s in samples:
        retrieved_set = set(s.retrieved_chunk_indices[:k])
        truth_set = set(s.ground_truth_chunk_indices)
        if not truth_set:
            continue
        recall = len(retrieved_set & truth_set) / len(truth_set)
        recalls.append(recall)
    return mean(recalls) if recalls else 0.0


def citation_precision(samples: list[EvalSample]) -> float:
    """Of the cited chunks, how many are actually in the ground truth?"""
    precisions = []
    for s in samples:
        cited = set(s.cited_chunk_indices)
        truth = set(s.ground_truth_chunk_indices)
        if not cited:
            continue
        precisions.append(len(cited & truth) / len(cited))
    return mean(precisions) if precisions else 0.0


def citation_recall(samples: list[EvalSample]) -> float:
    """Of the ground-truth chunks, how many were cited?"""
    recalls = []
    for s in samples:
        cited = set(s.cited_chunk_indices)
        truth = set(s.ground_truth_chunk_indices)
        if not truth:
            continue
        recalls.append(len(cited & truth) / len(truth))
    return mean(recalls) if recalls else 0.0


def compute_all_metrics(samples: list[EvalSample]) -> dict:
    """Compute all evaluation metrics and return as a dictionary."""
    return {
        "retrieval_recall@5": retrieval_recall_at_k(samples, k=5),
        "retrieval_recall@10": retrieval_recall_at_k(samples, k=10),
        "citation_precision": citation_precision(samples),
        "citation_recall": citation_recall(samples),
        "num_samples": len(samples),
    }
