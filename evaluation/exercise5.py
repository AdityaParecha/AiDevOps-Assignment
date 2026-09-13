import json
import time
import requests
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================

APP_URL = "http://127.0.0.1:8000/ask"
RAG_URL = "http://127.0.0.1:8001/retrieve"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

MODELS = [
    "gemma3:1b",
    "mistral:latest",
    "granite4.2:latest"
]

QUESTIONS = [
    {
        "id": "Q01",
        "question": "What is reactive autoscaling?"
    },
    {
        "id": "Q04",
        "question": "What can happen when there is a sudden traffic spike and the system relies only on reactive scaling?"
    },
    {
        "id": "Q07",
        "question": "What scale-down approach is recommended when traffic temporarily decreases?"
    },
    {
        "id": "Q10",
        "question": "What is the difference between reactive scaling and pre-scaling?"
    },
    {
        "id": "Q20",
        "question": "Why might adding more replicas fail to solve every latency problem?"
    }
]

OUTPUT_FILE = "exercise5_comparison.json"


# ============================================================
# HELPERS
# ============================================================

def get_answer(data):
    """Support either 'answer' or 'response' depending on service schema."""
    return data.get("answer") or data.get("response") or ""


# ============================================================
# RETRIEVE CONTEXT DIRECTLY
# ============================================================

def retrieve_context(question):
    """
    Calls the existing RAG service directly so that the exact
    retrieved context used for Exercise 5 is saved in JSON.
    """

    response = requests.post(
        RAG_URL,
        json={
            "question": question,
            "n_results": 3
        },
        timeout=120
    )

    response.raise_for_status()
    data = response.json()

    return {
        "context": data.get("context", ""),
        "sources": data.get("sources", []),
        "distances": data.get("distances", [])
    }


# ============================================================
# WITH CONTEXT
# ============================================================

def call_with_context(question, model):
    """
    Uses the existing application /ask endpoint.

    The RAG context is retrieved separately above only so we can
    record the actual context in the experiment JSON.
    """

    start = time.perf_counter()

    response = requests.post(
        APP_URL,
        json={
            "question": question,
            "model": model
        },
        timeout=600
    )

    latency_ms = (time.perf_counter() - start) * 1000

    response.raise_for_status()
    data = response.json()

    return {
        "condition": "with_context",
        "latency_ms": round(latency_ms, 2),
        "answer": get_answer(data),
        "model": data.get("model", model),
        "prompt_tokens": data.get("prompt_tokens"),
        "output_tokens": data.get("output_tokens"),
        "total_tokens": data.get("total_tokens"),
        "generation_time_ms": data.get("generation_time_ms")
    }


# ============================================================
# WITHOUT CONTEXT
# ============================================================

def call_without_context(question, model):
    """
    Calls Ollama directly.

    No RAG retrieval and no retrieved context are supplied.
    """

    start = time.perf_counter()

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": model,
            "prompt": question,
            "stream": False
        },
        timeout=600
    )

    latency_ms = (time.perf_counter() - start) * 1000

    response.raise_for_status()
    data = response.json()

    prompt_tokens = data.get("prompt_eval_count")
    output_tokens = data.get("eval_count")

    return {
        "condition": "without_context",
        "latency_ms": round(latency_ms, 2),
        "answer": data.get("response", ""),
        "model": model,
        "prompt_tokens": prompt_tokens,
        "output_tokens": output_tokens,
        "total_tokens": (
            (prompt_tokens or 0) + (output_tokens or 0)
        ),
        "generation_time_ms": (
            data.get("eval_duration", 0) / 1_000_000
            if data.get("eval_duration")
            else None
        )
    }


# ============================================================
# MAIN
# ============================================================

def main():

    results = {
        "experiment": "Exercise 5 - RAG Context Comparison",
        "description": (
            "Comparison of three LLM models on five questions "
            "with and without retrieved RAG context."
        ),
        "models": MODELS,
        "questions": QUESTIONS,
        "total_experiments": len(MODELS) * len(QUESTIONS) * 2,
        "results": []
    }

    total = len(MODELS) * len(QUESTIONS) * 2
    current = 0

    for model in MODELS:

        print("\n" + "=" * 70)
        print(f"MODEL: {model}")
        print("=" * 70)

        for q in QUESTIONS:

            qid = q["id"]
            question = q["question"]

            print(f"\n{qid}: {question}")

            # ------------------------------------------------
            # RETRIEVE CONTEXT
            # ------------------------------------------------

            try:
                print("  Retrieving context...")

                retrieval = retrieve_context(question)

                print(
                    "  Sources:",
                    retrieval["sources"]
                )

            except Exception as e:

                print(f"  RAG ERROR: {e}")

                retrieval = {
                    "context": "",
                    "sources": [],
                    "distances": [],
                    "error": str(e)
                }

            # ------------------------------------------------
            # WITH CONTEXT
            # ------------------------------------------------

            print("  [1/2] WITH context...")

            try:

                result = call_with_context(
                    question,
                    model
                )

                results["results"].append({
                    "question_id": qid,
                    "question": question,
                    "model": model,
                    "condition": "with_context",

                    "retrieved_context": retrieval["context"],
                    "sources": retrieval["sources"],
                    "distances": retrieval["distances"],

                    "answer": result["answer"],
                    "latency_ms": result["latency_ms"],
                    "prompt_tokens": result["prompt_tokens"],
                    "output_tokens": result["output_tokens"],
                    "total_tokens": result["total_tokens"],
                    "generation_time_ms": result["generation_time_ms"]
                })

                current += 1

                print(
                    f"       Answer captured "
                    f"({result['latency_ms']:.2f} ms)"
                )

            except Exception as e:

                results["results"].append({
                    "question_id": qid,
                    "question": question,
                    "model": model,
                    "condition": "with_context",
                    "retrieved_context": retrieval["context"],
                    "sources": retrieval["sources"],
                    "distances": retrieval["distances"],
                    "answer": "",
                    "error": str(e)
                })

                current += 1
                print(f"       ERROR: {e}")

            # ------------------------------------------------
            # WITHOUT CONTEXT
            # ------------------------------------------------

            print("  [2/2] WITHOUT context...")

            try:

                result = call_without_context(
                    question,
                    model
                )

                results["results"].append({
                    "question_id": qid,
                    "question": question,
                    "model": model,
                    "condition": "without_context",

                    "retrieved_context": "",
                    "sources": [],
                    "distances": [],

                    "answer": result["answer"],
                    "latency_ms": result["latency_ms"],
                    "prompt_tokens": result["prompt_tokens"],
                    "output_tokens": result["output_tokens"],
                    "total_tokens": result["total_tokens"],
                    "generation_time_ms": result["generation_time_ms"]
                })

                current += 1

                print(
                    f"       Answer captured "
                    f"({result['latency_ms']:.2f} ms)"
                )

            except Exception as e:

                results["results"].append({
                    "question_id": qid,
                    "question": question,
                    "model": model,
                    "condition": "without_context",
                    "retrieved_context": "",
                    "sources": [],
                    "distances": [],
                    "answer": "",
                    "error": str(e)
                })

                current += 1
                print(f"       ERROR: {e}")

            print(f"  Progress: {current}/{total}")

    # ========================================================
    # SAVE JSON
    # ========================================================

    output_path = Path(OUTPUT_FILE)

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            results,
            f,
            indent=2,
            ensure_ascii=False
        )

    print("\n" + "=" * 70)
    print("EXERCISE 5 COMPLETE")
    print("=" * 70)
    print(f"Total experiments: {total}")
    print(f"Saved to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
