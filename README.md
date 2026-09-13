# AI DevOps Assistant

A local, containerized AI DevOps assistant built incrementally across **Week 3 and Week 4**. The project demonstrates the progression from a direct local LLM application to a knowledge-grounded RAG system, then to a multi-service Dockerized architecture, followed by systematic model evaluation and repository-level codebase understanding using Sourcegraph.

The system is designed to answer questions about **autoscaling, scaling policies, and scaling incidents** using a local knowledge base. It runs locally using **Ollama**, **ChromaDB**, **FastAPI**, and **Docker Compose**, without requiring a cloud LLM API for the core application.

---

## Table of Contents

- [1. Project Overview](#1-project-overview)
- [2. Objectives](#2-objectives)
- [3. Final Architecture](#3-final-architecture)
- [4. Technology Stack](#4-technology-stack)
- [5. Repository Structure](#5-repository-structure)
- [6. Prerequisites](#6-prerequisites)
- [7. Environment Setup](#7-environment-setup)
- [8. Ollama Setup](#8-ollama-setup)
- [9. ChromaDB / Knowledge Base Setup](#9-chromadb--knowledge-base-setup)
- [10. Week 3](#10-week-3)
  - [Exercise 1 — Basic LLM Application](#exercise-1--basic-llm-application)
  - [Exercise 2 — Knowledge Base](#exercise-2--knowledge-base)
  - [Exercise 3 — Retrieval-Augmented Generation](#exercise-3--retrieval-augmented-generation-rag)
- [11. Week 4](#11-week-4)
  - [Exercise 4 — APIs and Microservices](#exercise-4--apis-and-microservices)
  - [Exercise 5 — Dockerization and Evaluation](#exercise-5--dockerization-and-evaluation)
  - [Exercise 6 — Repository-Level Codebase Understanding](#exercise-6--repository-level-codebase-understanding)
- [12. API Reference](#12-api-reference)
- [13. Running the Final Dockerized System](#13-running-the-final-dockerized-system)
- [14. Running the Frontend](#14-running-the-frontend)
- [15. Model Evaluation Methodology](#15-model-evaluation-methodology)
- [16. Evaluation Results](#16-evaluation-results)
- [17. Exercise 5 RAG Context Comparison](#17-exercise-5-rag-context-comparison)
- [18. Exercise 6 Sourcegraph Integration](#18-exercise-6-sourcegraph-integration)
- [19. Security and Configuration](#19-security-and-configuration)
- [20. Troubleshooting](#20-troubleshooting)
- [21. Design Decisions and Important Details](#21-design-decisions-and-important-details)
- [22. Limitations](#22-limitations)
- [23. Key Findings](#23-key-findings)
- [24. Future Improvements](#24-future-improvements)
- [25. Conclusion](#25-conclusion)

---

# 1. Project Overview

The AI DevOps Assistant is a local AI system that combines:

- a browser-based frontend,
- a FastAPI application service,
- a retrieval service,
- ChromaDB as a local vector database,
- a dedicated LLM service,
- Ollama as the local model runtime,
- Docker Compose for service orchestration, and
- Sourcegraph for repository-level code retrieval during Exercise 6.

The knowledge base focuses on autoscaling concepts and incidents, including:

- reactive autoscaling,
- Horizontal Pod Autoscaler (HPA),
- delays during sudden traffic spikes,
- aggressive scale-down behavior,
- bottlenecks that CPU utilization may not reveal,
- predictive/pre-scaling, and
- scaling policies for temporary traffic fluctuations.

The project was developed around a local Windows environment. Ollama runs on the Windows host while the application services run inside Docker containers.

---

# 2. Objectives

The project progressively demonstrates the following concepts:

1. Communicating with a local LLM through Ollama.
2. Building a domain-specific knowledge base.
3. Creating embeddings for knowledge-base chunks.
4. Storing and retrieving vectors using ChromaDB.
5. Building a Retrieval-Augmented Generation (RAG) pipeline.
6. Separating the system into independently deployable services.
7. Exposing functionality through HTTP APIs.
8. Containerizing services using Docker.
9. Orchestrating containers using Docker Compose.
10. Comparing multiple local LLMs using a common evaluation dataset.
11. Measuring latency, token consumption, CPU, memory, retrieval recall, completion, and answer quality.
12. Evaluating repository-level understanding across multiple files and services.
13. Using Sourcegraph as a repository-code retrieval/reference layer for cross-file questions.

---

# 3. Final Architecture

## 3.1 Runtime Architecture

```text
                         USER
                           |
                           v
                 +------------------+
                 |     Frontend     |
                 |    HTML/CSS/JS   |
                 +--------+---------+
                          |
                          | HTTP POST /ask
                          v
                 +------------------+
                 | Application      |
                 | Service :8000    |
                 +--------+---------+
                          |
                +---------+---------+
                |                   |
                | POST /retrieve    | POST /generate
                v                   v
       +----------------+   +----------------+
       | RAG Service    |   | LLM Service    |
       | :8001          |   | :8002          |
       +-------+--------+   +-------+--------+
               |                    |
               v                    |
        +-------------+             |
        |  ChromaDB   |             |
        | Vector DB    |             |
        +------+------+             |
               |                    |
               +---------+----------+
                         |
                         v
                +-------------------+
                | Ollama            |
                | Windows Host      |
                | :11434            |
                +---------+---------+
                          |
                    +-----+-----+
                    |           |
                    v           v
             nomic-embed-text  Selected LLM
```

## 3.2 Request Flow

A normal user request follows this sequence:

```text
1. Frontend sends POST /ask
          |
          v
2. Application Service receives question
          |
          v
3. Application Service calls RAG Service
          |
          v
4. RAG Service embeds the question
          |
          v
5. ChromaDB returns relevant chunks
          |
          v
6. RAG Service returns context + sources
          |
          v
7. Application Service calls LLM Service
          |
          v
8. LLM Service sends question + context + selected model to Ollama
          |
          v
9. Ollama generates the answer
          |
          v
10. Application Service returns answer + metrics + sources
```

---

# 4. Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| Language | Python 3.11 | Application and evaluation code |
| API framework | FastAPI | HTTP microservices |
| ASGI server | Uvicorn | Runs FastAPI services |
| HTTP client | Requests | Service-to-service communication and evaluation |
| LLM runtime | Ollama | Runs local LLMs |
| Embedding model | `nomic-embed-text` | Converts text into vector embeddings |
| Vector database | ChromaDB | Stores and searches embeddings |
| Frontend | HTML, CSS, JavaScript | Browser chat interface |
| Containerization | Docker | Isolates application services |
| Orchestration | Docker Compose | Runs the three services together |
| Repository retrieval | Sourcegraph | Cross-file code retrieval for Exercise 6 |
| Environment management | Conda / Python virtual environment | Local development |

The core Python dependencies are listed in `requirements.txt`:

```text
requests
fastapi
uvicorn
chromadb
ollama
```

Exercise 6 additionally requires `python-dotenv` for loading Sourcegraph/Ollama configuration from `.env`.

---

# 5. Repository Structure

```text
Devops assignment/
│
├── app.py
├── rag.py
├── without_rag.py
├── process_knowledge.py
│
├── requirements.txt
├── docker-compose.yml
├── Dockerfile.application
├── Dockerfile.rag
├── Dockerfile.llm
├── .gitignore
├── README.md
│
├── knowledge_base/
│   ├── hpa_basics.txt
│   ├── scaling_incidents.txt
│   └── scaling_policy.txt
│
├── chroma_db/
│   └── ... local/generated ChromaDB data
│
├── services/
│   ├── application_service.py
│   ├── rag_service.py
│   └── llm_service.py
│
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── style.css
│
└── evaluation/
    ├── questions.json
    ├── models.json
    ├── evaluate.py
    ├── analyze_results.py
    ├── results.csv
    ├── results_final.csv
    ├── model_summary.csv
    ├── exercise5.py
    ├── exercise5_comparison.json
    ├── exercise6.py
    └── exercise6_results.json
```

### Important generated/local files

`chroma_db/` contains local vector-store data. Depending on how the project is shared or zipped, this directory may be absent even though it is required by the Dockerized RAG service. If it is missing, regenerate it using `process_knowledge.py` as described below.

`.env` is intentionally not included in the repository because it contains the Sourcegraph access token.

---

# 6. Prerequisites

The project is intended for Windows and requires:

- Python 3.11
- Conda (recommended, but a normal Python virtual environment also works)
- Ollama
- Docker Desktop
- Git (recommended)
- A modern browser

For Exercise 6:

- a running Sourcegraph instance,
- a Sourcegraph access token,
- the GitHub repository indexed in Sourcegraph,
- Python package `python-dotenv`.

---

# 7. Environment Setup

## 7.1 Open the project

```powershell
cd "..\Devops assignment"
```

Use the actual location of the repository if it is different on your machine.

## 7.2 Create the Python environment

```powershell
conda create -n ai-devops python=3.11
```

Activate it:

```powershell
conda activate ai-devops
```

## 7.3 Install project dependencies

```powershell
pip install -r requirements.txt
```

For Exercise 6 also install:

```powershell
pip install python-dotenv
```

---

# 8. Ollama Setup

Ollama is the local model runtime used by the project.

Check installation:

```powershell
ollama --version
```

Check installed models:

```powershell
ollama list
```

## 8.1 Embedding model

The RAG system uses:

```text
nomic-embed-text
```

Install it if necessary:

```powershell
ollama pull nomic-embed-text
```

## 8.2 Models used in evaluation

The repository's evaluation configuration contains these nine models:

| Model | Approx. size in `models.json` |
|---|---:|
| `gemma3:1b` | 0.815 GB |
| `qwen3.5:0.8b` | 1.000 GB |
| `mistral:latest` | 4.400 GB |
| `hermes3:latest` | 4.700 GB |
| `dolphin3:latest` | 4.900 GB |
| `rnj-1:latest` | 5.100 GB |
| `qwen3:latest` | 5.200 GB |
| `qwen3.5:4b-q8_0` | 5.300 GB |
| `granite4.2:latest` | 5.300 GB |

Pull whichever models you need before running the evaluation. For example:

```powershell
ollama pull gemma3:1b
ollama pull mistral:latest
ollama pull granite4.2:latest
```

For the complete nine-model evaluation, pull all nine models listed above.

> **Important:** Older project notes referred to Code Llama. The current evaluation and service implementation use the models configured in `models.json` and the request passed to `LLM Service`. Do not assume Code Llama is the current default model.

## 8.3 Verify Ollama

```powershell
Invoke-WebRequest http://localhost:11434/api/tags
```

Ollama must remain running while the Dockerized application is being used.

---

# 9. ChromaDB / Knowledge Base Setup

The knowledge base consists of three text files:

```text
knowledge_base/
├── hpa_basics.txt
├── scaling_incidents.txt
└── scaling_policy.txt
```

The vector database is stored locally under:

```text
chroma_db/
```

## 9.1 Build / regenerate ChromaDB

If `chroma_db/` is missing or you want to regenerate the database:

```powershell
cd ".\Devops assignment"
python .\process_knowledge.py
```

The script:

1. Reads `.txt` files from `knowledge_base/`.
2. Splits each document into chunks.
3. Uses a chunk size of 500 characters with 50-character overlap.
4. Generates embeddings using `nomic-embed-text`.
5. Stores chunks, embeddings, and source metadata in the `devops_knowledge` Chroma collection.

Expected high-level flow:

```text
knowledge_base/*.txt
        |
        v
   Text Chunking
        |
        v
nomic-embed-text
        |
        v
     ChromaDB
```

## 9.2 Important Docker detail

The RAG Dockerfile copies the Chroma directory into the image, while `docker-compose.yml` also mounts the local directory:

```yaml
volumes:
  - ./chroma_db:/app/chroma_db
```

Therefore, when running the final Docker Compose setup, the local `chroma_db/` directory should exist and contain the `devops_knowledge` collection.

---

# 10. Week 3

Week 3 establishes the core AI pipeline: direct LLM usage, knowledge preparation, embeddings, retrieval, and RAG.

---

## Exercise 1 — Basic LLM Application

### Goal

The first stage demonstrates how a Python application communicates directly with a locally running LLM through Ollama.

### File

```text
app.py
```

### Architecture

```text
User
 |
 v
app.py
 |
 v
Ollama :11434
 |
 v
Selected model configured in app.py
 |
 v
Response
```

The script accepts questions interactively until the user enters `exit`.

### Run

Make sure Ollama is running, then:

```powershell
python .\app.py
```

Enter a question. Type:

```text
exit
```

to stop.

### What this exercise demonstrates

- Local LLM inference.
- HTTP communication with Ollama.
- Sending a prompt to a model.
- Receiving and displaying generated text.
- The baseline architecture before RAG is introduced.

---

## Exercise 2 — Knowledge Base

### Goal

Introduce domain-specific knowledge so the assistant can later ground its answers in project-provided information rather than relying only on the model's general knowledge.

### Knowledge files

```text
knowledge_base/hpa_basics.txt
knowledge_base/scaling_incidents.txt
knowledge_base/scaling_policy.txt
```

### Processing file

```text
process_knowledge.py
```

### Processing pipeline

```text
Text Documents
      |
      v
Chunking
      |
      v
nomic-embed-text
      |
      v
Embeddings
      |
      v
ChromaDB
```

### Chunking strategy

The current implementation uses:

```text
chunk_size = 500 characters
overlap = 50 characters
```

The overlap helps preserve information across chunk boundaries.

### Stored metadata

Each Chroma entry stores the source filename as metadata, allowing the retrieval service to return source information along with the context.

### Run

```powershell
python .\process_knowledge.py
```

The script prints the number of documents processed and chunks stored.

---

## Exercise 3 — Retrieval-Augmented Generation (RAG)

### Goal

Introduce retrieval between the user's question and the LLM so the model receives relevant knowledge-base context.

### File

```text
rag.py
```

### RAG architecture

```text
Question
   |
   v
Question Embedding
   |
   v
ChromaDB Similarity Search
   |
   v
Top Relevant Chunks
   |
   v
Context Construction
   |
   v
LLM Prompt
   |
   v
Ollama
   |
   v
Answer
```

The script retrieves three results by default.

### Retrieval details

`rag.py`:

1. Connects to Ollama.
2. Generates an embedding for the question using `nomic-embed-text:latest`.
3. Queries the `devops_knowledge` Chroma collection.
4. Retrieves documents, distances, and metadata.
5. Concatenates the retrieved documents into context.
6. Adds the context and user question to a RAG prompt.
7. Sends the prompt to the configured generation model.

### Run

```powershell
python .\rag.py
```

### Baseline comparison

The project also contains:

```text
without_rag.py
```

This script sends the question directly to the LLM without retrieving the project knowledge base.

Therefore:

```text
WITHOUT RAG
Question -> LLM -> Answer
```

versus:

```text
WITH RAG
Question -> Embedding -> ChromaDB -> Context -> LLM -> Answer
```

This provides the conceptual baseline for evaluating the benefit of retrieval.

---

# 11. Week 4

Week 4 extends the Week 3 prototype into a service-oriented, containerized and evaluated system. It also introduces repository-level code understanding through Sourcegraph.

---

## Exercise 4 — APIs and Microservices

### Goal

Separate the application into independent services with clear responsibilities and HTTP APIs.

### Services

```text
services/
├── application_service.py
├── rag_service.py
└── llm_service.py
```

### Service responsibilities

#### Application Service — port 8000

File:

```text
services/application_service.py
```

Endpoint:

```text
POST /ask
```

Responsibilities:

1. Receive the user's question.
2. Call the RAG service.
3. Receive retrieved context and sources.
4. Call the LLM service.
5. Pass the selected model to the LLM service.
6. Return the final answer, sources, token metrics, model and generation timing.

The service uses:

```text
RAG_SERVICE_URL = http://rag-service:8001/retrieve
LLM_SERVICE_URL = http://llm-service:8002/generate
```

#### RAG Service — port 8001

File:

```text
services/rag_service.py
```

Endpoint:

```text
POST /retrieve
```

Responsibilities:

1. Receive a question.
2. Generate its embedding using `nomic-embed-text`.
3. Query ChromaDB.
4. Retrieve relevant documents.
5. Return combined context.
6. Return source filenames and Chroma distances.

#### LLM Service — port 8002

File:

```text
services/llm_service.py
```

Endpoint:

```text
POST /generate
```

Responsibilities:

1. Receive the question.
2. Receive retrieved context.
3. Receive the selected model name.
4. Build the grounding prompt.
5. Call Ollama.
6. Return the generated response and token/generation metrics.

### Microservice flow

```text
POST /ask
    |
    v
Application Service :8000
    |
    +------ POST /retrieve ------> RAG Service :8001
    |                                  |
    |                                  v
    |                              ChromaDB
    |                                  |
    |<--------- context --------------+
    |
    +------ POST /generate -----> LLM Service :8002
                                      |
                                      v
                               Ollama :11434
                                      |
                                      v
                                  LLM model
                                      |
    |<--------- answer ---------------+
    |
    v
Final JSON response
```

---

## Exercise 5 — Dockerization and Evaluation

Exercise 5 contains two important parts: containerizing the service architecture and systematically evaluating the model pipeline.

### 5.1 Dockerization

Dockerfiles:

```text
Dockerfile.application
Dockerfile.rag
Dockerfile.llm
```

Docker Compose file:

```text
docker-compose.yml
```

### Container layout

```text
application-service  -> :8000
rag-service          -> :8001
llm-service          -> :8002
```

### Ollama remains on the host

Ollama is not containerized in the current setup. The two services that need direct Ollama access use:

```text
http://host.docker.internal:11434
```

The Compose file provides the host mapping using:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

This is important because `127.0.0.1` inside a Docker container refers to the container itself, not the Windows host.

### Build containers

```powershell
docker compose build
```

### Start services

```powershell
docker compose up
```

### Stop services

```powershell
docker compose down
```

### Check containers

```powershell
docker ps
```

### Check logs

```powershell
docker compose logs
```

Individual services:

```powershell
docker compose logs application-service
docker compose logs rag-service
docker compose logs llm-service
```

---

# 12. API Reference

## 12.1 Application Service

Base URL:

```text
http://127.0.0.1:8000
```

### `GET /`

Health/status endpoint.

Example:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/
```

### `POST /ask`

Request:

```json
{
  "question": "Why can reactive autoscaling be slow during a sudden traffic spike?",
  "model": "mistral:latest"
}
```

The `model` field has a default in the current application service, but supplying it explicitly is recommended for evaluation or reproducibility.

PowerShell example:

```powershell
$body = @{
    question = "Why can reactive autoscaling be slow during a sudden traffic spike?"
    model = "mistral:latest"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/ask" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

The final response contains fields such as:

```json
{
  "question": "...",
  "answer": "...",
  "model": "...",
  "sources": [],
  "prompt_tokens": 0,
  "output_tokens": 0,
  "total_tokens": 0,
  "generation_time_ms": 0
}
```

The actual numeric values depend on the request and selected model.

---

## 12.2 RAG Service

Base URL:

```text
http://127.0.0.1:8001
```

### `POST /retrieve`

Request:

```json
{
  "question": "What is reactive autoscaling?",
  "n_results": 3
}
```

The response contains:

- combined retrieved context,
- source filenames, and
- retrieval distances.

The application service uses this output to construct the LLM request.

---

## 12.3 LLM Service

Base URL:

```text
http://127.0.0.1:8002
```

### `GET /`

Returns service status.

### `POST /generate`

Request structure:

```json
{
  "question": "What is reactive autoscaling?",
  "context": "Retrieved knowledge-base context...",
  "model": "mistral:latest"
}
```

The service calls Ollama and returns:

- generated response,
- model name,
- prompt tokens,
- output tokens,
- total tokens,
- generation time in milliseconds.

---

# 13. Running the Final Dockerized System

Follow these steps in order.

## Step 1 — Start Docker Desktop

Verify Docker:

```powershell
docker version
docker compose version
```

## Step 2 — Start Ollama

```powershell
ollama list
```

Make sure the required embedding and generation models are installed.

## Step 3 — Verify ChromaDB

Check that:

```text
chroma_db/
```

exists and contains the Chroma data.

If missing, regenerate:

```powershell
python .\process_knowledge.py
```

## Step 4 — Build containers

```powershell
cd "C:\coding\Devops assignment"
docker compose build
```

## Step 5 — Start containers

```powershell
docker compose up
```

The expected services are:

```text
Application Service : http://localhost:8000
RAG Service         : http://localhost:8001
LLM Service         : http://localhost:8002
```

## Step 6 — Test the application API

In another PowerShell window:

```powershell
$body = @{
    question = "What can happen when there is a sudden traffic spike and the system relies only on reactive scaling?"
    model = "mistral:latest"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/ask" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

If the response contains an answer, sources and metrics, the complete backend pipeline is working.

---

# 14. Running the Frontend

The frontend is located at:

```text
frontend/
├── index.html
├── script.js
└── style.css
```

The JavaScript sends requests to:

```text
http://127.0.0.1:8000/ask
```

The simplest development approach is to open the frontend using VS Code Live Server.

For example, with Live Server it may be available at:

```text
http://127.0.0.1:5500/frontend/
```

The exact port depends on the local Live Server configuration.

### Frontend flow

```text
Browser
   |
   | POST /ask
   v
Application Service
   |
   v
RAG + LLM pipeline
   |
   v
Answer
   |
   v
Browser chat interface
```

The frontend does not perform vector search or LLM inference itself; it acts as the user-facing client.

---

# 15. Model Evaluation Methodology

The evaluation pipeline is implemented under:

```text
evaluation/
```

The main evaluation script is:

```text
evaluation/evaluate.py
```

The analysis script is:

```text
evaluation/analyze_results.py
```

## 15.1 Evaluation dataset

The dataset contains:

- **25 questions**
- **20 answerable questions**
- **5 deliberately unanswerable questions**
- **9 local LLM models**
- **225 total model-question evaluations**

```text
25 questions × 9 models = 225 evaluations
```

### Question categories currently present

- `basic`
- `incident`
- `policy`
- `comparison`
- `unanswerable`

The answerable questions cover concepts such as reactive autoscaling, traffic spikes, scaling delays, scale-down policy, bottlenecks and predictive scaling.

The unanswerable questions deliberately ask for information that is not contained in the knowledge base, including:

1. Exact Kubernetes version.
2. Exact memory limit per application pod.
3. Cloud provider.
4. Database engine.
5. System administrator name.

This allows the experiment to test whether a model refuses to fabricate missing information.

## 15.2 Metrics collected

The evaluation CSV records fields for:

### Response/performance

- latency in milliseconds,
- generation time,
- prompt tokens,
- output tokens,
- total tokens.

### Retrieval

- retrieved source files,
- retrieval distances,
- expected source files,
- retrieval recall.

### Resource usage

- CPU baseline,
- CPU peak,
- memory baseline,
- memory peak.

### Quality-related fields

The CSV schema also contains fields for:

- correctness,
- relevance,
- factual claims,
- unsupported claims,
- hallucination rate.

These claim-level fields were not populated in the final evaluation dataset, so they are **not presented as measured hallucination percentages**.

## 15.3 Evaluation execution

The evaluator calls:

```text
http://127.0.0.1:8000/ask
```

and passes a model name with every question.

The script is designed to resume work using already completed `(model, question_id)` pairs and writes each result immediately to CSV.

Run:

```powershell
cd "C:\coding\Devops assignment\evaluation"
python .\evaluate.py
```

Results are stored in:

```text
evaluation/results.csv
```

The cleaned/final evaluation artifact is:

```text
evaluation/results_final.csv
```

## 15.4 Model-wise analysis

Run:

```powershell
python .\analyze_results.py
```

The generated summary is:

```text
evaluation/model_summary.csv
```

---

# 16. Evaluation Results

The final evaluation artifact contains 225 runs across 9 models.

The following table is based on the repository's saved analysis artifacts.

| Model | Quality* | Avg Latency | Avg Total Tokens | CPU Peak | Memory Peak | Retrieval Recall | Blank Answers |
|---|---:|---:|---:|---:|---:|---:|---:|
| `granite4.2:latest` | 98.0% | 41.16 s | 1049.84 | 47.26% | 73.28% | 0.85 | 0 |
| `rnj-1:latest` | 95.3% | 7.49 s | 477.00 | 50.77% | 87.08% | 0.85 | 0 |
| `qwen3:latest` | 95.2% | 19.75 s | 671.12 | 48.28% | 79.51% | 0.85 | 0 |
| `qwen3.5:4b-q8_0` | 93.0% | 78.50 s | 1768.04 | 48.54% | 78.61% | 0.85 | 1 |
| `mistral:latest` | 89.9% | 5.02 s | 539.76 | 58.78% | 95.20% | 0.85 | 0 |
| `dolphin3:latest` | 87.5% | 4.86 s | 441.00 | 56.03% | 90.71% | 0.85 | 0 |
| `hermes3:latest` | 85.7% | 5.53 s | 457.28 | 46.62% | 91.38% | 0.85 | 0 |
| `gemma3:1b` | 70.1% | 1.17 s | 423.92 | 30.45% | 73.48% | 0.85 | 0 |
| `qwen3.5:0.8b` | 33.3% | 28.86 s | 3649.56 | 20.63% | 79.32% | 0.85 | 15 |

\* **Quality is a source-grounded rubric score**, not a formal claim-level accuracy or hallucination measurement. The detailed methodology is documented in `exercise4_report.md`.

## 16.1 Retrieval result

Average retrieval recall is **0.85 for every model**.

This is expected because all models use the same RAG retrieval pipeline and the same retrieval configuration. The LLM model changes the generation stage, not the underlying Chroma retrieval operation.

Consequently, differences between models in this experiment are primarily generation/response differences rather than different retrieval results.

## 16.2 Quality

The highest source-grounded rubric score was:

```text
granite4.2:latest -> 98.0%
```

Next:

```text
rnj-1:latest      -> 95.3%
qwen3:latest      -> 95.2%
qwen3.5:4b-q8_0   -> 93.0%
```

The weakest result was:

```text
qwen3.5:0.8b -> 33.3%
```

The weak result is strongly associated with its **15 blank answers out of 25**.

## 16.3 Latency

The fastest model in the saved results was:

```text
gemma3:1b -> 1169.98 ms average latency
```

The slowest was:

```text
qwen3.5:4b-q8_0 -> 78504.65 ms average latency
```

This demonstrates that increasing model size does not automatically provide an efficient deployment choice for a latency-sensitive local application.

## 16.4 Resource usage

Lowest recorded average peak CPU:

```text
qwen3.5:0.8b -> 20.63%
```

Lowest recorded average peak memory:

```text
granite4.2:latest -> 73.28%
```

However, low resource usage alone is not sufficient to select a model. `qwen3.5:0.8b` had the lowest average CPU usage but also the weakest quality/completion behavior.

## 16.5 Unanswerable questions

The five unanswerable questions test whether the system avoids inventing information.

All models except `qwen3.5:0.8b` completed all five refusal cases without a blank response. The saved analysis reports an overall unanswerable-refusal behavior of:

```text
granite4.2:latest   100%
rnj-1:latest        100%
qwen3:latest        100%
qwen3.5:4b-q8_0     100%
mistral:latest       80%
dolphin3:latest      60%
hermes3:latest       40%
gemma3:1b            40%
qwen3.5:0.8b         60%
```

These percentages should be interpreted in conjunction with the blank-answer/completion behavior and the rubric methodology in `exercise4_report.md`.

A formal claim-level hallucination rate was **not measured**, because `total_factual_claims`, `unsupported_claims`, and `hallucination_rate_pct` are blank in the final CSV.

## 16.6 Quality versus latency

The results demonstrate a clear trade-off:

- `granite4.2:latest` has the highest quality score but around 41 seconds average latency.
- `gemma3:1b` is dramatically faster but has lower quality.
- `rnj-1:latest` provides a strong middle ground with 95.3% rubric quality and 7.49 seconds average latency.
- `mistral:latest` and `dolphin3:latest` provide roughly 5-second average latency with mid-to-high quality scores.

There is therefore no single universally optimal model. Selection depends on whether the application prioritizes maximum answer quality, latency, resource usage, or balance.

---

# 17. Exercise 5 RAG Context Comparison

The repository also contains a focused Exercise 5 experiment:

```text
evaluation/exercise5.py
evaluation/exercise5_comparison.json
```

It compares three models:

```text
gemma3:1b
mistral:latest
granite4.2:latest
```

under two conditions:

```text
with_context
without_context
```

using five representative questions:

```text
Q01
Q04
Q07
Q10
Q20
```

This produces:

```text
3 models × 5 questions × 2 conditions = 30 experiments
```

## Purpose

The experiment isolates the effect of retrieved context.

### Without context

```text
Question -> LLM -> Answer
```

### With context

```text
Question
   |
   v
RAG Retrieval
   |
   v
Retrieved Context
   |
   v
LLM
   |
   v
Answer
```

The saved JSON contains the retrieved context, sources, answers, model, condition and timing/token information for each experiment.

Run the experiment with:

```powershell
cd "C:\coding\Devops assignment\evaluation"
python .\exercise5.py
```

The existing saved artifact can also be inspected directly:

```text
evaluation/exercise5_comparison.json
```

---

# 18. Exercise 6 — Repository-Level Codebase Understanding

Exercise 6 evaluates a different capability from the original knowledge-base RAG experiment: **understanding relationships between multiple files, services and components in the repository**.

The repository used for Sourcegraph indexing is:

```text
github.com/AdityaParecha/AiDevOps-Assignment
```

The six questions are designed around cross-file relationships such as:

1. Complete request flow from frontend to LLM response.
2. Files/services involved in RAG retrieval.
3. Ollama communication and model selection.
4. What happens inside `/ask`.
5. What changes if the RAG service URL changes.
6. How Application, RAG, LLM, Docker and Ollama are connected.

## 18.1 Why Sourcegraph?

The original ChromaDB RAG system retrieves **domain knowledge** from text documents. It is not a repository-code search engine.

Exercise 6 therefore introduces Sourcegraph as a **code-aware retrieval/reference layer**. Sourcegraph searches the indexed GitHub repository and supplies relevant code snippets to the LLM.

Conceptually:

```text
Repository Code
      |
      v
Sourcegraph Search
      |
      v
Relevant Files / Line Matches
      |
      v
Repository Context
      |
      v
Local LLM via Ollama
      |
      v
Repository-Level Answer
```

This should not be confused with the Week 3 ChromaDB knowledge-base RAG pipeline.

## 18.2 Sourcegraph setup

A local Sourcegraph server was used on port `7080`.

The GraphQL endpoint is:

```text
http://localhost:7080/.api/graphql
```

The repository was connected through the GitHub code host connection and indexed in Sourcegraph.

The expected repository path used in search queries is:

```text
github.com/AdityaParecha/AiDevOps-Assignment
```

## 18.3 `.env` configuration

Create:

```text
C:\coding\Devops assignment\.env
```

Example:

```env
SOURCEGRAPH_URL=http://localhost:7080/.api/graphql
SOURCEGRAPH_TOKEN=YOUR_SOURCEGRAPH_TOKEN
SOURCEGRAPH_REPO=github.com/AdityaParecha/AiDevOps-Assignment

OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=mistral:latest
```

Replace:

```text
YOUR_SOURCEGRAPH_TOKEN
```

with your own Sourcegraph access token.

**Never commit `.env` or the token to Git.** `.gitignore` already excludes `.env` and `.env.*`.

## 18.4 Run Exercise 6

From the project root:

```powershell
cd "C:\coding\Devops assignment"
python .\evaluation\exercise6.py
```

The script:

1. Loads Sourcegraph/Ollama settings from `.env`.
2. Searches Sourcegraph using repository-restricted queries.
3. Collects file paths and line previews.
4. Builds a repository-context prompt.
5. Sends that context to the configured Ollama model.
6. Saves every completed question immediately.

Output:

```text
evaluation/exercise6_results.json
```

## 18.5 Sourcegraph GraphQL search

The script uses the GraphQL endpoint and searches the repository with queries such as:

```text
repo:github.com/AdityaParecha/AiDevOps-Assignment application_service
```

The GraphQL response is handled through the nested `SearchResults` structure, with actual file matches accessed from the nested result list.

The retrieved evidence includes:

- file path,
- matching line number,
- line preview.

## 18.6 LLM grounding instructions

Exercise 6 instructs the LLM to:

- use only supplied repository evidence,
- avoid inventing files/functions/services/endpoints/ports,
- name relevant files,
- identify relevant functions/endpoints,
- explain relationships between components, and
- explicitly say `Insufficient repository evidence.` when the evidence is insufficient.

This makes the experiment focused on evidence-grounded repository reasoning rather than general software-development knowledge.

## 18.7 Important limitation of the current retrieval approach

Sourcegraph returns matching snippets rather than automatically giving the entire repository to the LLM. Therefore, the quality of a cross-file answer depends on whether the search terms retrieve enough relevant evidence.

For example, an answer can be technically correct about a service but still miss an important relationship if the relevant file was not retrieved.

This is a retrieval-and-reasoning problem distinct from the ChromaDB knowledge-base retrieval problem.

---

# 19. Security and Configuration

## `.env`

Exercise 6 uses a Sourcegraph access token. Keep it in `.env`:

```text
SOURCEGRAPH_TOKEN=...
```

Do not place the token directly into `exercise6.py`.

## `.gitignore`

The project ignores:

```text
.env
.env.*
__pycache__/
*.py[cod]
chroma_db/
```

This prevents local secrets, Python cache files and generated ChromaDB data from being accidentally committed.

## Sourcegraph token

Use a token with only the permissions required to read the repository. Never paste the token into public documentation, GitHub commits, screenshots or chat messages.

---

# 20. Troubleshooting

## 20.1 Ollama is not reachable

Check:

```powershell
ollama list
```

Then:

```powershell
Invoke-WebRequest http://localhost:11434/api/tags
```

If Docker services cannot reach Ollama, verify that they use:

```text
host.docker.internal:11434
```

rather than:

```text
127.0.0.1:11434
```

inside the containers.

---

## 20.2 ChromaDB collection does not exist

If the RAG service reports that `devops_knowledge` does not exist, regenerate the vector database:

```powershell
python .\process_knowledge.py
```

Then restart Docker Compose:

```powershell
docker compose down
docker compose up --build
```

---

## 20.3 Docker cannot connect to Ollama

Check that Ollama is running on Windows.

Then inspect the service logs:

```powershell
docker compose logs rag-service --tail=50
docker compose logs llm-service --tail=50
```

The Docker Compose configuration explicitly maps:

```text
host.docker.internal -> host-gateway
```

for the RAG and LLM containers.

---

## 20.4 `/ask` returns HTTP 500

Inspect:

```powershell
docker compose logs application-service --tail=50
docker compose logs rag-service --tail=50
docker compose logs llm-service --tail=50
```

The request path is:

```text
/ask
 -> /retrieve
 -> /generate
 -> Ollama
```

Therefore, a failure can originate in any stage.

---

## 20.5 Frontend cannot connect

Make sure:

```powershell
docker ps
```

shows the application service.

Then test:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/
```

The frontend JavaScript currently calls:

```text
http://127.0.0.1:8000/ask
```

---

## 20.6 Exercise 6 says Sourcegraph token is missing

Check that `.env` exists in the project root:

```text
C:\coding\Devops assignment\.env
```

and contains:

```env
SOURCEGRAPH_TOKEN=YOUR_TOKEN
```

Also make sure `python-dotenv` is installed:

```powershell
pip install python-dotenv
```

---

## 20.7 Sourcegraph GraphQL error

Exercise 6 uses the nested GraphQL search-result structure. If Sourcegraph reports a GraphQL schema error, verify that the local Sourcegraph version exposes the expected search fields and that the endpoint is:

```text
http://localhost:7080/.api/graphql
```

Also verify that the repository is indexed before running the script.

---

# 21. Design Decisions and Important Details

## 21.1 Why three services?

The application, retrieval and generation responsibilities are separated so each component has a clear role:

```text
Application Service -> orchestration
RAG Service         -> retrieval
LLM Service         -> generation
```

This reduces coupling and makes individual services easier to test and replace.

## 21.2 Why keep Ollama on the host?

The current project uses Ollama natively on Windows. Running it outside Docker avoids putting the local model runtime inside the service containers.

The containers access it through:

```text
host.docker.internal:11434
```

## 21.3 Why ChromaDB?

ChromaDB provides a local vector store suitable for a small knowledge base. It allows the application to store embeddings and perform similarity-based retrieval without requiring a cloud vector database.

## 21.4 Why source metadata?

The RAG service returns both context and source filenames. This makes it possible to inspect where retrieved information came from and enables retrieval-recall analysis in the evaluation pipeline.

## 21.5 Why include unanswerable questions?

A RAG assistant should not confidently invent information that is absent from its supplied knowledge base. The five unanswerable questions explicitly test this behavior.

## 21.6 Why evaluate multiple models?

Local deployment introduces practical trade-offs. A model with higher answer quality may also have significantly higher latency or resource consumption. The evaluation measures these trade-offs instead of selecting a model only by subjective output quality.

---

# 22. Limitations

1. The knowledge base is intentionally small and focused on autoscaling/scaling incidents.
2. ChromaDB is local rather than a production-grade distributed vector database.
3. Ollama runs on the local host, so model performance depends heavily on local hardware.
4. The model evaluation measures latency and system resource usage on the local machine; these values are environment-specific.
5. Retrieval recall is based on expected source filenames, so it measures source retrieval rather than semantic answer correctness.
6. A code test-pass metric is not applicable to the 25-question DevOps dataset because the questions do not ask the model to produce executable code that is automatically tested.
7. Claim-level hallucination percentages were not measured because the manual claim annotation fields were not populated.
8. Exercise 6 retrieves repository snippets using keyword-based Sourcegraph searches; incomplete retrieval can limit repository-level reasoning.
9. Sourcegraph is used as the code retrieval/reference layer in Exercise 6 and is separate from the ChromaDB knowledge-base RAG pipeline.
10. The current service URLs are hardcoded in the application service rather than being fully externalized through environment variables.

---

# 23. Key Findings

The project demonstrates several important findings.

### Finding 1 — RAG separates knowledge retrieval from generation

The retrieval layer provides the LLM with project-specific context instead of relying only on the model's internal knowledge.

### Finding 2 — Retrieval was consistent across the tested models

All nine evaluated models had an average retrieval recall of **0.85**, because they shared the same retrieval pipeline.

### Finding 3 — Higher quality can come with significant latency

`granite4.2:latest` achieved the highest source-grounded rubric score at **98.0%**, but its average latency was approximately **41.16 seconds**.

### Finding 4 — Small models can be much faster but are not automatically better

`gemma3:1b` averaged approximately **1.17 seconds**, but its rubric quality was **70.1%**.

### Finding 5 — `rnj-1:latest` was a strong quality/latency compromise

It achieved **95.3%** rubric quality with approximately **7.49 seconds** average latency.

### Finding 6 — Resource efficiency alone is not enough

`qwen3.5:0.8b` had the lowest average peak CPU usage at **20.63%**, but it also produced **15 blank responses** and had the lowest rubric quality.

### Finding 7 — Repository-level understanding is a separate problem

Understanding a multi-service codebase requires retrieving relationships across files, configuration and service boundaries. Exercise 6 therefore uses Sourcegraph code retrieval rather than treating the existing text knowledge base as a substitute for repository search.

---

# 24. Future Improvements

Potential next steps include:

1. Move service URLs and model defaults into environment variables.
2. Add health-check endpoints to every service.
3. Add Docker health checks and stronger startup dependency handling.
4. Add structured logging and request IDs across services.
5. Add automated tests for all API endpoints.
6. Add an automated semantic evaluation framework for answer correctness.
7. Add human-annotated factual claims to calculate a defensible hallucination rate.
8. Add executable code-generation questions and automated test-pass evaluation.
9. Improve Sourcegraph retrieval by retrieving larger file sections around matches.
10. Add repository symbol/dependency-aware retrieval for Exercise 6.
11. Add a dedicated reranking stage to improve RAG retrieval precision.
12. Add persistent evaluation dashboards and experiment versioning.
13. Containerize Ollama/model serving separately if the deployment environment supports it.
14. Add authentication and stricter CORS configuration for production deployment.
15. Add streaming responses for a better interactive user experience.

---

# 25. Conclusion

The project demonstrates the complete progression from a simple local LLM application to a modular, retrieval-augmented and containerized AI DevOps assistant.

The progression can be summarized as:

```text
WEEK 3

Direct LLM
   |
   v
Knowledge Base
   |
   v
Embeddings + ChromaDB
   |
   v
RAG

        |
        v

WEEK 4

Microservices
   |
   v
FastAPI APIs
   |
   v
Docker + Docker Compose
   |
   v
Multi-model Evaluation
   |
   v
Sourcegraph Repository Retrieval
   |
   v
Cross-file Codebase Understanding
```

The final system combines **local LLM inference, vector retrieval, API-based service separation, Docker orchestration, quantitative evaluation, and repository-level code retrieval** into one end-to-end project.

The evaluation also demonstrates why model selection is a deployment decision rather than simply a search for the model with the highest answer score: quality, latency, token consumption and resource usage must be considered together.

---

## Quick Start — Short Version

For an already configured machine:

```powershell
cd "C:\coding\Devops assignment"
conda activate ai-devops
ollama list
```

If ChromaDB is missing:

```powershell
python .\process_knowledge.py
```

Build and start the backend:

```powershell
docker compose up --build
```

Test:

```powershell
$body = @{
    question = "Why can reactive autoscaling be slow during a sudden traffic spike?"
    model = "mistral:latest"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/ask" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

For evaluation:

```powershell
cd .\evaluation
python .\evaluate.py
python .\analyze_results.py
```

For Exercise 6, create `.env` with the Sourcegraph configuration and run:

```powershell
python .\exercise6.py
```

Results are saved under:

```text
evaluation/
```

---

**Project:** AI DevOps Assistant  
**Core stack:** Python 3.11 · FastAPI · ChromaDB · Ollama · Docker Compose · Sourcegraph  
**Deployment style:** Local / Windows host + Dockerized application services
