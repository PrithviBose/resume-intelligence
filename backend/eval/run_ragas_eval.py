"""
RAGAS evaluation script for the fixed-chain RAG pipeline (POST /api/query).

WHAT THIS DOES
    Loads the hand-written questions in `golden_set.json`, asks the *real*
    running API each one (exactly like ResumeChat.tsx does), then scores every
    answer with RAGAS's four core metrics:
        - faithfulness       : does the answer only state things the retrieved
                                 chunks actually support? (hallucination check)
        - answer_relevancy   : does the answer actually address the question?
        - context_precision  : were the retrieved chunks relevant, and ranked well?
        - context_recall     : did retrieval find everything needed to answer,
                                 compared to the hand-written reference answer?
    See docs/progress.html -> "RAGAS Evaluation" for the full explanation of
    what each metric measures and how it's computed internally.

WHY THIS FILE LIVES OUTSIDE app/
    This is an offline analysis tool, not a running part of the API:
        - It makes several extra LLM calls per question (RAGAS's metrics are
          "LLM-as-judge" — each one calls a judge model internally, sometimes
          more than once per metric), so a run can take minutes and cost real
          Azure OpenAI tokens.
        - It must never be imported by, or triggered from, the FastAPI request
          path. Keeping all of it under backend/eval/ (sibling to app/, not
          inside it) makes that boundary physically obvious, and keeps the
          eval-only dependencies (ragas, langchain-community — see
          requirements.txt) mentally separate from the app's runtime deps.

HOW TO RUN
    1. Start the backend normally in one terminal:
           cd backend && uvicorn app.main:app --reload --port 8000
    2. Fill in backend/eval/golden_set.json with a real resume_id (see
       GET /api/users) and real reference answers for that resume.
    3. In another terminal, from the backend/ directory, with the venv active:
           python -m eval.run_ragas_eval
       (Must be run as a module with `-m`, not `python eval/run_ragas_eval.py`,
       so Python puts backend/ on sys.path and `import app...` below resolves.)

DEPENDENCY GOTCHA (kept here so future-you doesn't have to re-debug it)
    `import ragas` transitively imports `langchain_community.chat_models.vertexai`
    at package-init time, regardless of which LLM provider you actually use.
    langchain-community >=0.4 reorganized that module and removed it, which
    breaks the bare `import ragas` with a ModuleNotFoundError. Fix: requirements.txt
    pins `langchain-community==0.3.31`. Safe to try relaxing that pin if a future
    ragas release fixes the internal import.

WHY THE JUDGE LLM/EMBEDDINGS ARE BUILT DIRECTLY HERE, NOT VIA LANGCHAIN WRAPPERS
    RAGAS's newer `ragas.metrics.collections` + `ragas.llms.llm_factory` API (used
    below) accepts a plain `openai.AsyncAzureOpenAI` client directly — no need for
    LangChain's `AzureChatOpenAI` wrapper. That keeps this script's *own* code
    free of LangChain, even though `ragas` itself still depends on it internally
    (see the gotcha above). Same idea for embeddings: `ragas.embeddings.HuggingFaceEmbeddings`
    reuses the exact local BGE model `embedding_service.py` already loads for
    retrieval, so answer_relevancy doesn't need a separate Azure embedding deployment.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

import httpx
from openai import AsyncAzureOpenAI
from ragas.embeddings import HuggingFaceEmbeddings
from ragas.llms import llm_factory
from ragas.metrics.collections import (
    AnswerRelevancy,
    ContextPrecisionWithReference,
    ContextRecall,
    Faithfulness,
)

from app.lib.config import settings

EVAL_DIR = Path(__file__).resolve().parent
GOLDEN_SET_PATH = EVAL_DIR / "golden_set.json"
RESULTS_DIR = EVAL_DIR / "results"

# Both optional — see the "RAGAS evaluation" block in backend/.env.example.
API_BASE_URL = os.getenv("RAGAS_API_BASE_URL", "http://127.0.0.1:8000")
JUDGE_DEPLOYMENT_NAME = (
    os.getenv("RAGAS_JUDGE_DEPLOYMENT_NAME") or settings.azure_openai_deployment_name
)

METRIC_NAMES = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]


@dataclass
class GoldenQuestion:
    question: str
    reference: str


@dataclass
class EvalRow:
    question: str
    reference: str
    answer: str
    contexts: list[str]
    scores: dict[str, float]


def load_golden_set() -> tuple[str, int, list[GoldenQuestion]]:
    """Read golden_set.json. Keys starting with '_' (like "_instructions") are
    documentation for humans only and are ignored here on purpose."""
    raw = json.loads(GOLDEN_SET_PATH.read_text(encoding="utf-8"))
    resume_id = raw["resume_id"]
    top_k = raw.get("top_k", 3)
    questions = [GoldenQuestion(question=q["question"], reference=q["reference"]) for q in raw["questions"]]

    if resume_id == "REPLACE_WITH_A_REAL_RESUME_ID":
        raise SystemExit(
            "golden_set.json still has the placeholder resume_id.\n"
            "Fill in a real resume_id (call GET /api/users to find one) before running this script."
        )
    return resume_id, top_k, questions


async def fetch_answer(
    client: httpx.AsyncClient, resume_id: str, question: str, top_k: int
) -> tuple[str, list[str]]:
    """Call the app's own POST /api/query — the same request ResumeChat.tsx makes —
    so the eval measures exactly what a real user gets, not an internal shortcut."""
    response = await client.post(
        f"{API_BASE_URL}/api/query",
        json={"resume_id": resume_id, "query": question, "top_k": top_k},
        timeout=60.0,
    )
    response.raise_for_status()
    body = response.json()
    contexts = [source["text"] for source in body["sources"]]
    return body["answer"], contexts


def build_metrics(llm, embeddings) -> dict[str, object]:
    """One instance of each metric, reused across every question — they hold no
    per-question state, just the llm/embeddings handed to them here."""
    return {
        "faithfulness": Faithfulness(llm=llm),
        "answer_relevancy": AnswerRelevancy(llm=llm, embeddings=embeddings),
        "context_precision": ContextPrecisionWithReference(llm=llm),
        "context_recall": ContextRecall(llm=llm),
    }


async def score_row(
    metrics: dict[str, object],
    question: str,
    reference: str,
    answer: str,
    contexts: list[str],
) -> dict[str, float]:
    """Run all four metrics for one question concurrently. Each metric makes its
    own independent judge-LLM call(s) (faithfulness even makes two: decompose
    the answer into claims, then check each claim), so there's no benefit to
    running them one after another."""
    faithfulness_result, relevancy_result, precision_result, recall_result = await asyncio.gather(
        metrics["faithfulness"].ascore(
            user_input=question, response=answer, retrieved_contexts=contexts
        ),
        metrics["answer_relevancy"].ascore(user_input=question, response=answer),
        metrics["context_precision"].ascore(
            user_input=question, reference=reference, retrieved_contexts=contexts
        ),
        metrics["context_recall"].ascore(
            user_input=question, retrieved_contexts=contexts, reference=reference
        ),
    )
    return {
        "faithfulness": faithfulness_result.value,
        "answer_relevancy": relevancy_result.value,
        "context_precision": precision_result.value,
        "context_recall": recall_result.value,
    }


def print_report(rows: list[EvalRow]) -> None:
    print("\n=== RAGAS Evaluation Report ===")
    for i, row in enumerate(rows, start=1):
        print(f"\n[{i}] {row.question}")
        for name in METRIC_NAMES:
            print(f"    {name:<18}: {row.scores[name]:.3f}")

    print("\n--- Averages across all questions ---")
    for name in METRIC_NAMES:
        avg = mean(row.scores[name] for row in rows)
        print(f"    {name:<18}: {avg:.3f}")


def save_report(resume_id: str, rows: list[EvalRow]) -> Path:
    """Every run is saved as its own timestamped JSON file (never overwritten)
    so scores can be compared across runs as you tweak prompts/chunking/top_k —
    the same "compare traces over time" idea used with Langfuse, applied to
    quality scores instead of latency/cost."""
    RESULTS_DIR.mkdir(exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_path = RESULTS_DIR / f"ragas_run_{timestamp}.json"

    payload = {
        "resume_id": resume_id,
        "api_base_url": API_BASE_URL,
        "judge_deployment": JUDGE_DEPLOYMENT_NAME,
        "timestamp": timestamp,
        "averages": {
            name: mean(row.scores[name] for row in rows) for name in METRIC_NAMES
        },
        "rows": [
            {
                "question": row.question,
                "reference": row.reference,
                "answer": row.answer,
                "contexts": row.contexts,
                "scores": row.scores,
            }
            for row in rows
        ],
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path


async def main() -> None:
    resume_id, top_k, golden_questions = load_golden_set()

    # Reuses the exact Azure credentials the app already uses for generation
    # (app/lib/config.py) — no separate secrets to manage just for evaluation.
    azure_client = AsyncAzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )
    judge_llm = llm_factory(JUDGE_DEPLOYMENT_NAME, provider="openai", client=azure_client)

    # Reuses the same local BGE model embedding_service.py already loads for
    # retrieval, instead of requiring a separate Azure embedding deployment
    # just so RAGAS's answer_relevancy metric has something to embed with.
    judge_embeddings = HuggingFaceEmbeddings(model=settings.embedding_model_name)

    metrics = build_metrics(judge_llm, judge_embeddings)

    rows: list[EvalRow] = []
    async with httpx.AsyncClient() as client:
        for i, golden_question in enumerate(golden_questions, start=1):
            print(f"[{i}/{len(golden_questions)}] {golden_question.question}")
            try:
                answer, contexts = await fetch_answer(
                    client, resume_id, golden_question.question, top_k
                )
                scores = await score_row(
                    metrics, golden_question.question, golden_question.reference, answer, contexts
                )
            except Exception as exc:  # one bad question shouldn't kill the whole run
                print(f"    SKIPPED — {exc}")
                continue

            rows.append(
                EvalRow(
                    question=golden_question.question,
                    reference=golden_question.reference,
                    answer=answer,
                    contexts=contexts,
                    scores=scores,
                )
            )

    if not rows:
        raise SystemExit("No questions were successfully evaluated — see SKIPPED reasons above.")

    print_report(rows)
    saved_to = save_report(resume_id, rows)
    print(f"\nFull per-question results saved to: {saved_to}")


if __name__ == "__main__":
    asyncio.run(main())
