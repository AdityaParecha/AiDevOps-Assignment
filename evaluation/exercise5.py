import json
import time
import requests
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================

APP_URL = "http://127.0.0.1:8000/ask"

# Choose 3 models for comparison
MODELS = [
    "gemma3:1b",
    "mistral:latest",
    "granite4.2:latest"
]

# Five representative questions from Exercise 3
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
# CALL EXISTING APPLICATION
# ============================================================

def call_with_context(question, model):
    """
    Existing RAG pipeline:
    frontend/application -> RAG -> context -> LLM
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
        "latency_ms": latency_ms,
        "response": data
    }


# ============================================================
# CALL LLM WITHOUT RAG
# ============================================================

def call_without_context(question, model):
    """
    Direct Ollama call.
    No RAG retrieval and no retrieved context.
    """

    start = time.perf_counter()

    response = requests.post(
        "http://127.0.0.1:11434/api/generate",
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

    return {
        "condition": "without_context",
        "latency_ms": latency_ms,
        "response": data
    }


# ============================================================
# NORMALIZE WITH-CONTEXT RESULT
# ============================================================

def normalize_with_context(result):
    data = result["response"]

    return {
        "condition": result["condition"],
        "latency_ms": round(result["latency_ms"], 2),

        "answer": data.get("response", ""),

        "retrieved_context": data.get("context", ""),

        "sources": data.get("sources", []),

        "distances": data.get("distances", []),

        "model": data.get("model", ""),

        "prompt_tokens": data.get("prompt_tokens"),
        "output_tokens": data.get("output_tokens"),
        "total_tokens": data.get("total_tokens"),

        "generation_time_ms": data.get("generation_time_ms")
    }


# ============================================================
# NORMALIZE WITHOUT-CONTEXT RESULT
# ============================================================

def normalize_without_context(result, model):
    data = result["response"]

    return {
        "condition": result["condition"],
        "latency_ms": round(result["latency_ms"], 2),

        "answer": data.get("response", ""),

        "retrieved_context": "",

        "sources": [],

        "distances": [],

        "model": model,

        "prompt_tokens": data.get("prompt_eval_count"),
        "output_tokens": data.get("eval_count"),

        "total_tokens": (
            (data.get("prompt_eval_count") or 0)
            + (data.get("eval_count") or 0)
        ),

        "generation_time_ms": (
            data.get("eval_duration", 0) / 1_000_000
            if data.get("eval_duration")
            else None
        )
    }


# ============================================================
# MAIN EXPERIMENT
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

            question_id = q["id"]
            question = q["question"]

            print(f"\n{question_id}: {question}")

            # ------------------------------------------------
            # WITH CONTEXT
            # ------------------------------------------------

            print("  [1/2] Running WITH context...")

            try:

                result = call_with_context(
                    question,
                    model
                )

                normalized = normalize_with_context(result)

                results["results"].append({
                    "question_id": question_id,
                    "question": question,
                    "model": model,
                    **normalized
                })

                current += 1

                print(
                    f"       Done "
                    f"({normalized['latency_ms']:.2f} ms)"
                )

            except Exception as e:

                results["results"].append({
                    "question_id": question_id,
                    "question": question,
                    "model": model,
                    "condition": "with_context",
                    "error": str(e)
                })

                current += 1

                print(f"       ERROR: {e}")

            # ------------------------------------------------
            # WITHOUT CONTEXT
            # ------------------------------------------------

            print("  [2/2] Running WITHOUT context...")

            try:

                result = call_without_context(
                    question,
                    model
                )

                normalized = normalize_without_context(
                    result,
                    model
                )

                results["results"].append({
                    "question_id": question_id,
                    "question": question,
                    "model": model,
                    **normalized
                })

                current += 1

                print(
                    f"       Done "
                    f"({normalized['latency_ms']:.2f} ms)"
                )

            except Exception as e:

                results["results"].append({
                    "question_id": question_id,
                    "question": question,
                    "model": model,
                    "condition": "without_context",
                    "error": str(e)
                })

                current += 1

                print(f"       ERROR: {e}")

            print(
                f"  Progress: {current}/{total}"
            )

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
    print("EXPERIMENT COMPLETE")
    print("=" * 70)

    print(f"Total experiments: {total}")
    print(f"Results saved to: {output_path.resolve()}")


if __name__ == "__main__":
    main()