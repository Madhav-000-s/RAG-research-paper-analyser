"""Evaluation runner that tests the RAG system against QA pairs."""

import asyncio
import json
import re
import sys
from pathlib import Path

import httpx

from metrics import EvalSample, compute_all_metrics

BASE_URL = "http://localhost:8000/api"


async def upload_paper(client: httpx.AsyncClient, pdf_path: str) -> str:
    """Upload a paper and wait for it to be ready."""
    with open(pdf_path, "rb") as f:
        response = await client.post(
            f"{BASE_URL}/papers",
            files={"file": (Path(pdf_path).name, f, "application/pdf")},
        )
    response.raise_for_status()
    paper_id = response.json()["id"]

    # Poll until ready
    for _ in range(60):  # Max 5 minutes
        resp = await client.get(f"{BASE_URL}/papers/{paper_id}")
        status = resp.json()["status"]
        if status == "ready":
            return paper_id
        if status == "error":
            raise RuntimeError(f"Paper ingestion failed for {pdf_path}")
        await asyncio.sleep(5)

    raise TimeoutError(f"Paper {pdf_path} did not finish processing")


async def query_paper(
    client: httpx.AsyncClient,
    paper_id: str,
    question: str,
) -> dict:
    """Ask a question about a paper."""
    response = await client.post(
        f"{BASE_URL}/query",
        json={
            "paper_id": paper_id,
            "question": question,
            "llm_provider": "ollama",
            "top_k": 10,
            "rerank_top_n": 5,
        },
        timeout=120.0,
    )
    response.raise_for_status()
    return response.json()


async def run_evaluation(papers_dir: str = "papers") -> None:
    """Run the full evaluation pipeline."""
    # Load QA pairs
    qa_path = Path(__file__).parent / "qa_pairs.json"
    with open(qa_path) as f:
        qa_pairs = json.load(f)

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Check backend is running
        try:
            resp = await client.get("http://localhost:8000/health")
            resp.raise_for_status()
        except Exception:
            print("ERROR: Backend is not running at http://localhost:8000")
            sys.exit(1)

        # Upload papers
        paper_ids: dict[str, str] = {}
        papers_path = Path(__file__).parent / papers_dir

        for qa in qa_pairs:
            filename = qa["paper_filename"]
            if filename not in paper_ids:
                pdf_path = papers_path / filename
                if not pdf_path.exists():
                    print(f"WARNING: Paper {filename} not found in {papers_path}, skipping")
                    continue
                print(f"Uploading {filename}...")
                paper_ids[filename] = await upload_paper(client, str(pdf_path))
                print(f"  -> Paper ID: {paper_ids[filename]}")

        # Run queries and collect results
        samples: list[EvalSample] = []

        for qa in qa_pairs:
            filename = qa["paper_filename"]
            if filename not in paper_ids:
                continue

            print(f"\nQ: {qa['question']}")
            result = await query_paper(client, paper_ids[filename], qa["question"])

            # Extract citation indices from answer
            cited_refs = sorted(set(int(m) for m in re.findall(r"\[(\d+)\]", result["answer"])))
            cited_indices = [ref - 1 for ref in cited_refs if ref > 0]

            # Retrieve chunk indices from citations
            retrieved_indices = [c["chunk_index"] for c in result["citations"]]

            print(f"A: {result['answer'][:200]}...")
            print(f"   Citations: {len(result['citations'])}")

            samples.append(
                EvalSample(
                    question=qa["question"],
                    answer=result["answer"],
                    retrieved_chunk_indices=retrieved_indices,
                    cited_chunk_indices=cited_indices,
                    ground_truth_answer=qa["ground_truth_answer"],
                    ground_truth_chunk_indices=qa["ground_truth_chunk_indices"],
                )
            )

        # Compute metrics
        if not samples:
            print("\nNo samples evaluated. Add PDFs to the papers/ directory.")
            return

        metrics = compute_all_metrics(samples)

        print("\n" + "=" * 50)
        print("EVALUATION RESULTS")
        print("=" * 50)
        for key, value in metrics.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.3f}")
            else:
                print(f"  {key}: {value}")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(run_evaluation())
