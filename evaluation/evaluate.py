import csv
import json
import os
import sys
import time
from datetime import datetime

import requests

try:
    import psutil
except ImportError:
    psutil = None


# ============================================================
# CONFIGURATION
# ============================================================

APP_URL = os.getenv(
    "APP_URL",
    "http://127.0.0.1:8000/ask"
)

QUESTIONS_FILE = "questions.json"
MODELS_FILE = "models.json"
RESULTS_FILE = "results.csv"

REQUEST_TIMEOUT = 600


# ============================================================
# LOAD DATA
# ============================================================

with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
    questions = json.load(f)

with open(MODELS_FILE, "r", encoding="utf-8") as f:
    models = json.load(f)


# Sort from lightest to heaviest
models.sort(key=lambda x: x["size_gb"])


# ============================================================
# RESULT CSV HEADER
# ============================================================

FIELDNAMES = [
    "timestamp",
    "model",
    "question_id",
    "category",
    "question",
    "answer",
    "latency_ms",
    "prompt_tokens",
    "output_tokens",
    "total_tokens",
    "generation_time_ms",
    "retrieved_sources",
    "retrieval_distances",
    "expected_sources",
    "retrieval_recall",
    "correctness_0_1",
    "relevance_0_2",
    "total_factual_claims",
    "unsupported_claims",
    "hallucination_rate_pct",
    "cpu_baseline_pct",
    "cpu_peak_pct",
    "memory_baseline_pct",
    "memory_peak_pct",
    "error"
]


# ============================================================
# CREATE CSV IF IT DOESN'T EXIST
# ============================================================

if not os.path.exists(RESULTS_FILE):

    with open(
        RESULTS_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=FIELDNAMES
        )

        writer.writeheader()


# ============================================================
# READ ALREADY COMPLETED RESULTS
# ============================================================

completed = set()

with open(
    RESULTS_FILE,
    "r",
    newline="",
    encoding="utf-8"
) as f:

    reader = csv.DictReader(f)

    for row in reader:

        model = row.get("model", "")
        question_id = row.get("question_id", "")

        if model and question_id:
            completed.add(
                (model, question_id)
            )


print()
print("=" * 70)
print("AI DEVOPS ASSISTANT - MODEL EVALUATION")
print("=" * 70)

print()
print(f"Questions: {len(questions)}")
print(f"Models:    {len(models)}")
print(f"Completed: {len(completed)} result(s)")
print()

print("Model order:")
print("-" * 70)

for i, model in enumerate(models, start=1):

    print(
        f"{i}. {model['model']:<25} "
        f"{model['size_gb']:.3f} GB"
    )

print("=" * 70)
print()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_cpu_memory():

    if psutil is None:
        return None, None

    cpu = psutil.cpu_percent(interval=0.2)

    memory = psutil.virtual_memory().percent

    return cpu, memory


def calculate_retrieval_recall(
    expected_sources,
    retrieved_sources
):

    if not expected_sources:
        return ""

    if not retrieved_sources:
        return 0

    expected = set(expected_sources)

    retrieved = set(retrieved_sources)

    found = expected.intersection(retrieved)

    return round(
        len(found) / len(expected),
        3
    )


def append_result(row):

    with open(
        RESULTS_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=FIELDNAMES
        )

        writer.writerow(row)

        f.flush()


# ============================================================
# EVALUATION
# ============================================================

total_questions = len(questions)
total_models = len(models)

try:

    for model_index, model_info in enumerate(
        models,
        start=1
    ):

        model_name = model_info["model"]
        model_size = model_info["size_gb"]

        pending_questions = [
            q for q in questions
            if (model_name, q["id"]) not in completed
        ]

        if not pending_questions:

            print(
                f"[SKIP MODEL] {model_name} "
                f"→ all questions already completed."
            )

            continue


        print()
        print("=" * 70)
        print(
            f"MODEL {model_index}/{total_models}: "
            f"{model_name}"
        )
        print(
            f"Size: {model_size:.3f} GB"
        )
        print(
            f"Remaining questions: "
            f"{len(pending_questions)}"
        )
        print("=" * 70)


        for question_index, q in enumerate(
            pending_questions,
            start=1
        ):

            question_id = q["id"]

            print()
            print(
                f"[{question_index}/{len(pending_questions)}] "
                f"{question_id}"
            )

            print(
                f"Question: {q['question']}"
            )

            print(
                f"Model: {model_name}"
            )


            # ------------------------------------------------
            # CPU / MEMORY BEFORE REQUEST
            # ------------------------------------------------

            cpu_before, memory_before = (
                get_cpu_memory()
            )


            # ------------------------------------------------
            # SEND REQUEST
            # ------------------------------------------------

            start_time = time.perf_counter()

            try:

                response = requests.post(
                    APP_URL,
                    json={
                        "question": q["question"],
                        "model": model_name
                    },
                    timeout=REQUEST_TIMEOUT
                )

                latency_ms = (
                    time.perf_counter() - start_time
                ) * 1000

                response.raise_for_status()

                data = response.json()


                # ------------------------------------------------
                # CPU / MEMORY AFTER REQUEST
                # ------------------------------------------------

                cpu_after, memory_after = (
                    get_cpu_memory()
                )


                # ------------------------------------------------
                # EXTRACT RESPONSE
                # ------------------------------------------------

                answer = data.get(
                    "answer",
                    ""
                )

                retrieved_source_objects = (
                    data.get(
                        "sources",
                        []
                    )
                )


                # Sources may be dictionaries
                # or strings depending on service output.

                retrieved_sources = []

                retrieval_distances = []

                for source in retrieved_source_objects:

                    if isinstance(source, dict):

                        source_name = (
                            source.get(
                                "source",
                                source.get(
                                    "file",
                                    ""
                                )
                            )
                        )

                        distance = source.get(
                            "distance",
                            ""
                        )

                        if source_name:
                            retrieved_sources.append(
                                source_name
                            )

                        retrieval_distances.append(
                            distance
                        )

                    else:

                        retrieved_sources.append(
                            str(source)
                        )


                expected_sources = q.get(
                    "expected_sources",
                    []
                )


                retrieval_recall = (
                    calculate_retrieval_recall(
                        expected_sources,
                        retrieved_sources
                    )
                )


                # ------------------------------------------------
                # TOKEN METRICS
                # ------------------------------------------------

                prompt_tokens = data.get(
                    "prompt_tokens",
                    0
                )

                output_tokens = data.get(
                    "output_tokens",
                    0
                )

                total_tokens = data.get(
                    "total_tokens",
                    0
                )

                generation_time_ms = data.get(
                    "generation_time_ms",
                    0
                )


                # ------------------------------------------------
                # RESULT ROW
                # ------------------------------------------------

                row = {

                    "timestamp":
                        datetime.now().isoformat(
                            timespec="seconds"
                        ),

                    "model":
                        model_name,

                    "question_id":
                        question_id,

                    "category":
                        q["category"],

                    "question":
                        q["question"],

                    "answer":
                        answer,

                    "latency_ms":
                        round(
                            latency_ms,
                            2
                        ),

                    "prompt_tokens":
                        prompt_tokens,

                    "output_tokens":
                        output_tokens,

                    "total_tokens":
                        total_tokens,

                    "generation_time_ms":
                        round(
                            float(
                                generation_time_ms or 0
                            ),
                            2
                        ),

                    "retrieved_sources":
                        json.dumps(
                            retrieved_sources
                        ),

                    "retrieval_distances":
                        json.dumps(
                            retrieval_distances
                        ),

                    "expected_sources":
                        json.dumps(
                            expected_sources
                        ),

                    "retrieval_recall":
                        retrieval_recall,

                    # Manual evaluation fields
                    "correctness_0_1":
                        "",

                    "relevance_0_2":
                        "",

                    "total_factual_claims":
                        "",

                    "unsupported_claims":
                        "",

                    "hallucination_rate_pct":
                        "",

                    "cpu_baseline_pct":
                        (
                            round(
                                cpu_before,
                                2
                            )
                            if cpu_before is not None
                            else ""
                        ),

                    "cpu_peak_pct":
                        (
                            round(
                                max(
                                    cpu_before,
                                    cpu_after
                                ),
                                2
                            )
                            if cpu_before is not None
                            and cpu_after is not None
                            else ""
                        ),

                    "memory_baseline_pct":
                        (
                            round(
                                memory_before,
                                2
                            )
                            if memory_before is not None
                            else ""
                        ),

                    "memory_peak_pct":
                        (
                            round(
                                max(
                                    memory_before,
                                    memory_after
                                ),
                                2
                            )
                            if memory_before is not None
                            and memory_after is not None
                            else ""
                        ),

                    "error":
                        ""
                }


                # ------------------------------------------------
                # SAVE IMMEDIATELY
                # ------------------------------------------------

                append_result(row)

                completed.add(
                    (model_name, question_id)
                )


                print(
                    f"✓ Completed "
                    f"| {latency_ms:.0f} ms "
                    f"| {total_tokens} tokens "
                    f"| retrieval={retrieval_recall}"
                )


            except Exception as e:

                latency_ms = (
                    time.perf_counter() - start_time
                ) * 1000

                print(
                    f"✗ ERROR: {e}"
                )

                # Save errors too, so the failure is visible.
                # Remove this pair from completed so a rerun
                # will retry it.

                row = {

                    "timestamp":
                        datetime.now().isoformat(
                            timespec="seconds"
                        ),

                    "model":
                        model_name,

                    "question_id":
                        question_id,

                    "category":
                        q["category"],

                    "question":
                        q["question"],

                    "answer":
                        "",

                    "latency_ms":
                        round(
                            latency_ms,
                            2
                        ),

                    "prompt_tokens":
                        "",

                    "output_tokens":
                        "",

                    "total_tokens":
                        "",

                    "generation_time_ms":
                        "",

                    "retrieved_sources":
                        "",

                    "retrieval_distances":
                        "",

                    "expected_sources":
                        json.dumps(
                            q.get(
                                "expected_sources",
                                []
                            )
                        ),

                    "retrieval_recall":
                        "",

                    "correctness_0_1":
                        "",

                    "relevance_0_2":
                        "",

                    "total_factual_claims":
                        "",

                    "unsupported_claims":
                        "",

                    "hallucination_rate_pct":
                        "",

                    "cpu_baseline_pct":
                        "",

                    "cpu_peak_pct":
                        "",

                    "memory_baseline_pct":
                        "",

                    "memory_peak_pct":
                        "",

                    "error":
                        str(e)
                }

                append_result(row)


except KeyboardInterrupt:

    print()
    print()
    print("=" * 70)
    print("EVALUATION INTERRUPTED")
    print("=" * 70)
    print()
    print(
        "All completed results have already been saved."
    )
    print()
    print(
        "Run the same command again to resume."
    )
    print("=" * 70)

    sys.exit(0)


print()
print("=" * 70)
print("EVALUATION COMPLETE")
print("=" * 70)
print()
print(
    f"Results saved to: {RESULTS_FILE}"
)
print()