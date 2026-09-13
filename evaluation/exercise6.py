import os
import json
import requests
from dotenv import load_dotenv


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

SOURCEGRAPH_URL = os.getenv(
    "SOURCEGRAPH_URL",
    "http://localhost:7080/.api/graphql"
)

SOURCEGRAPH_TOKEN = os.getenv("SOURCEGRAPH_TOKEN")

SOURCEGRAPH_REPO = os.getenv(
    "SOURCEGRAPH_REPO",
    "github.com/AdityaParecha/AiDevOps-Assignment"
)

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "gemma3:1b"
)

OUTPUT_FILE = os.path.join(
    os.path.dirname(__file__),
    "exercise6_results.json"
)


# ============================================================
# EXERCISE 6 QUESTIONS
# ============================================================

QUESTIONS = [
    {
        "id": "Q1",
        "question": (
            "Trace the complete flow of a user question from the "
            "frontend/application entry point until the final LLM response. "
            "Mention the files, services, endpoints, and important function calls involved."
        ),
        "search_terms": [
            "application_service",
            "rag_service",
            "llm_service",
            "/ask",
            "/retrieve",
            "/generate"
        ]
    },

    {
        "id": "Q2",
        "question": (
            "Which files and services are involved in RAG retrieval? "
            "Explain how the question reaches ChromaDB and how relevant context "
            "is returned to the application."
        ),
        "search_terms": [
            "rag_service",
            "retrieve",
            "ChromaDB",
            "nomic-embed-text"
        ]
    },

    {
        "id": "Q3",
        "question": (
            "Which component communicates with Ollama, and how is the selected "
            "LLM model passed through the system?"
        ),
        "search_terms": [
            "ollama",
            "model",
            "generate"
        ]
    },

    {
        "id": "Q4",
        "question": (
            "What happens inside the /ask endpoint after a request containing "
            "a user question is received? Trace the important steps across services."
        ),
        "search_terms": [
            "/ask",
            "RAG_SERVICE_URL",
            "LLM_SERVICE_URL"
        ]
    },

    {
        "id": "Q5",
        "question": (
            "If the RAG service URL changes, which files or components need "
            "to be modified? Explain why."
        ),
        "search_terms": [
            "RAG_SERVICE_URL",
            "rag-service",
            "8001"
        ]
    },

    {
        "id": "Q6",
        "question": (
            "Explain how the application service, RAG service, LLM service, "
            "Docker containers, and Ollama are connected. Include relevant "
            "ports and host/container communication details."
        ),
        "search_terms": [
            "rag-service",
            "llm-service",
            "host.docker.internal",
            "11434"
        ]
    }
]


# ============================================================
# SOURCEGRAPH SEARCH
# ============================================================

def search_sourcegraph(search_query):
    """
    Search repository code using Sourcegraph GraphQL API.
    """

    if not SOURCEGRAPH_TOKEN:
        raise RuntimeError(
            "SOURCEGRAPH_TOKEN is missing from .env"
        )

    graphql_query = """
    query SearchCode($query: String!) {
        search(query: $query) {
            results {
                matchCount
                limitHit
                results {
                    __typename

                    ... on FileMatch {
                        file {
                            path
                        }

                        lineMatches {
                            lineNumber
                            preview
                        }
                    }
                }
            }
        }
    }
    """

    headers = {
        "Authorization": f"token {SOURCEGRAPH_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "query": graphql_query,
        "variables": {
            "query": search_query
        }
    }

    try:
        response = requests.post(
            SOURCEGRAPH_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        response.raise_for_status()

    except requests.RequestException as e:
        print(f"Search failed for '{search_query}':")
        print(e)
        return []

    try:
        data = response.json()
    except ValueError:
        print(
            f"Sourcegraph returned invalid JSON for '{search_query}'"
        )
        print(response.text[:1000])
        return []

    # --------------------------------------------------------
    # GraphQL errors
    # --------------------------------------------------------

    if "errors" in data:
        print(
            f"Search failed for '{search_query}':"
        )

        for error in data["errors"]:
            print(
                json.dumps(
                    error,
                    indent=2
                )
            )

        return []

    # --------------------------------------------------------
    # Safely navigate GraphQL response
    # --------------------------------------------------------

    try:
        search_results = data["data"]["search"]["results"]

        # The actual FileMatch objects are inside
        # search.results.results
        matches = search_results.get("results", [])

        return matches

    except (KeyError, TypeError) as e:

        print(
            f"Unexpected Sourcegraph response for '{search_query}':"
        )

        print(
            json.dumps(
                data,
                indent=2
            )[:3000]
        )

        return []


# ============================================================
# COLLECT REPOSITORY CONTEXT
# ============================================================

def collect_repository_context(search_terms):
    """
    Search multiple terms and combine repository evidence.
    """

    collected = {}

    for term in search_terms:

        # Restrict search to our repository
        query = f"repo:{SOURCEGRAPH_REPO} {term}"

        print(f"   Searching Sourcegraph: {term}")

        results = search_sourcegraph(query)

        print(
            f"   Found {len(results)} result(s)"
        )

        for result in results:

            # Only process FileMatch results
            if result.get("__typename") != "FileMatch":
                continue

            file_info = result.get("file", {})

            file_path = file_info.get(
                "path",
                "unknown"
            )

            line_matches = result.get(
                "lineMatches",
                []
            )

            if file_path not in collected:
                collected[file_path] = []

            for match in line_matches:

                line_number = match.get(
                    "lineNumber"
                )

                preview = match.get(
                    "preview",
                    ""
                )

                collected[file_path].append(
                    {
                        "line": line_number,
                        "preview": preview
                    }
                )

    # --------------------------------------------------------
    # Convert collected dictionary to readable context
    # --------------------------------------------------------

    context_parts = []

    for file_path, matches in collected.items():

        context_parts.append(
            f"\n===== FILE: {file_path} ====="
        )

        # Remove duplicate lines
        seen = set()

        for match in matches:

            key = (
                match["line"],
                match["preview"]
            )

            if key in seen:
                continue

            seen.add(key)

            context_parts.append(
                f"Line {match['line']}: "
                f"{match['preview']}"
            )

    context = "\n".join(context_parts)

    return context


# ============================================================
# OLLAMA
# ============================================================

def ask_ollama(question, repository_context):
    """
    Ask Ollama to answer using only Sourcegraph repository evidence.
    """

    if not repository_context.strip():

        return {
            "answer": "Insufficient repository evidence.",
            "prompt_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0
        }

    prompt = f"""
You are analyzing a software repository.

Answer the question ONLY using the repository evidence provided below.

Do not invent:
- files
- functions
- services
- endpoints
- ports
- dependencies
- implementation details

If the repository evidence is insufficient, explicitly say:

"Insufficient repository evidence."

When possible:
1. Name the relevant files.
2. Name relevant functions/endpoints.
3. Explain how the components interact.
4. Trace the flow across multiple files/services.
5. Distinguish directly supported facts from reasonable inference.

QUESTION:
{question}

REPOSITORY EVIDENCE:
{repository_context}

ANSWER:
"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }

    try:

        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=300
        )

        response.raise_for_status()

        data = response.json()

        return {
            "answer": data.get(
                "response",
                ""
            ),
            "prompt_tokens": data.get(
                "prompt_eval_count",
                0
            ),
            "output_tokens": data.get(
                "eval_count",
                0
            ),
            "total_tokens": (
                data.get("prompt_eval_count", 0)
                +
                data.get("eval_count", 0)
            )
        }

    except requests.RequestException as e:

        print(
            "Ollama request failed:"
        )

        print(e)

        return {
            "answer": f"Ollama request failed: {e}",
            "prompt_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0
        }

    except ValueError:

        print(
            "Ollama returned invalid JSON:"
        )

        print(
            response.text[:1000]
        )

        return {
            "answer": "Ollama returned invalid JSON.",
            "prompt_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0
        }


# ============================================================
# SAVE RESULTS
# ============================================================

def save_results(results):

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            results,
            f,
            indent=2,
            ensure_ascii=False
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("EXERCISE 6 - CODEBASE UNDERSTANDING")
    print("=" * 70)

    print(
        f"Repository : {SOURCEGRAPH_REPO}"
    )

    print(
        f"LLM        : {OLLAMA_MODEL}"
    )

    print(
        f"Sourcegraph : {SOURCEGRAPH_URL}"
    )

    print(
        f"Ollama      : {OLLAMA_URL}"
    )

    print("=" * 70)
    print()

    # --------------------------------------------------------
    # Check Sourcegraph token
    # --------------------------------------------------------

    if not SOURCEGRAPH_TOKEN:

        print(
            "ERROR: SOURCEGRAPH_TOKEN is not configured."
        )

        print(
            "Add it to your .env file."
        )

        return

    results = []

    # --------------------------------------------------------
    # Process every question
    # --------------------------------------------------------

    for index, item in enumerate(QUESTIONS, start=1):

        qid = item["id"]
        question = item["question"]

        print()
        print("-" * 70)
        print(
            f"{qid} ({index}/{len(QUESTIONS)})"
        )
        print(question)
        print("-" * 70)

        # ----------------------------------------------------
        # Step 1: Sourcegraph retrieval
        # ----------------------------------------------------

        print()
        print("[1] Retrieving repository context...")

        context = collect_repository_context(
            item["search_terms"]
        )

        print()

        print(
            f"Context size: {len(context)} characters"
        )

        # ----------------------------------------------------
        # Step 2: Send context to Ollama
        # ----------------------------------------------------

        print()

        print(
            "[2] Sending context to Ollama..."
        )

        llm_result = ask_ollama(
            question,
            context
        )

        answer = llm_result["answer"]

        # ----------------------------------------------------
        # Print answer
        # ----------------------------------------------------

        print()
        print("LLM ANSWER:")
        print(answer)

        # ----------------------------------------------------
        # Store result
        # ----------------------------------------------------

        result = {
            "question_id": qid,
            "question": question,
            "model": OLLAMA_MODEL,
            "sourcegraph_repo": SOURCEGRAPH_REPO,
            "search_terms": item["search_terms"],
            "context_characters": len(context),
            "repository_context": context,
            "answer": answer,
            "prompt_tokens": llm_result["prompt_tokens"],
            "output_tokens": llm_result["output_tokens"],
            "total_tokens": llm_result["total_tokens"]
        }

        results.append(result)

        # ----------------------------------------------------
        # Save immediately
        # ----------------------------------------------------

        save_results(results)

        print()
        print(
            f"Saved progress -> {OUTPUT_FILE}"
        )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("EXERCISE 6 COMPLETE")
    print("=" * 70)

    print(
        f"Questions evaluated : {len(results)}"
    )

    print(
        f"Results saved to     : {OUTPUT_FILE}"
    )

    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()