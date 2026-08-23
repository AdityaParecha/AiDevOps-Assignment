# AI DevOps Assistant — LLM, RAG, Microservices & Docker

A local AI-powered DevOps assistant built progressively through five exercises:

1. **Basic LLM Application**
2. **Knowledge Base**
3. **Retrieval + RAG**
4. **APIs, Services & Orchestration**
5. **Dockerization**

The application uses **Ollama** locally with **Code Llama** for response generation and **nomic-embed-text** for embeddings.

---

## 1. Project Overview

The final application answers DevOps questions using a local knowledge base about autoscaling, scaling policies, and scaling incidents.

```text
User / Frontend
       |
       v
Application Service :8000
       |
       v
RAG Service :8001
       |
       +----> ChromaDB
       |
       +----> Ollama / nomic-embed-text
       |
       v
Relevant Context
       |
       v
LLM Service :8002
       |
       v
Ollama / Code Llama
       |
       v
Final Response
```

Ollama runs on the Windows host, while the three application services run as Docker containers.

---

## 2. Technologies

- Python 3.11
- Conda
- FastAPI
- Uvicorn
- Requests
- Ollama
- Code Llama
- nomic-embed-text
- ChromaDB
- HTML / CSS / JavaScript
- Docker
- Docker Compose

---

## 3. Project Structure

```text
Devops assignment/
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── knowledge_base/
│   ├── hpa_basics.txt
│   ├── scaling_incidents.txt
│   └── scaling_policy.txt
│
├── chroma_db/
│   └── ... generated Chroma files
│
├── services/
│   ├── application_service.py
│   ├── rag_service.py
│   └── llm_service.py
│
├── app.py
├── rag.py
├── without_rag.py
├── process_knowledge.py
│
├── requirements.txt
│
├── Dockerfile.application
├── Dockerfile.rag
├── Dockerfile.llm
│
└── docker-compose.yml
```

---

# 4. Prerequisites

Install:

- Python 3.11
- Conda (recommended)
- Ollama
- Docker Desktop

The project was developed and tested on Windows.

---

# 5. Ollama Setup

Make sure Ollama is installed and running.

Check:

```powershell
ollama --version
```

Check installed models:

```powershell
ollama list
```

Required models:

```text
codellama
nomic-embed-text
```

Install them if necessary:

```powershell
ollama pull codellama
ollama pull nomic-embed-text
```

Test Ollama:

```powershell
ollama run codellama
```

---

# 6. Python Environment Setup

Go to the project directory:

```powershell
cd "..\Devops assignment"
```

Create the environment:

```powershell
conda create -n ai-devops python=3.11
```

Activate it:

```powershell
conda activate ai-devops
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

The requirements include the libraries needed by the services, such as:

```text
fastapi
uvicorn
requests
chromadb
ollama
```

---

# 7. Exercise 1 — Build the Basic LLM Application

## Objective

Understand how an application communicates with an LLM through Ollama.

Initial architecture:

```text
User
  |
  v
Application
  |
  v
Ollama API
  |
  v
Code Llama
  |
  v
Response
```

There is no RAG, vector database, or retrieval at this stage.

## Important file: `app.py`

The initial application accepts a user request, sends it to Ollama, uses Code Llama to generate a response, and returns that response.

The main concept is:

```text
Application -> Ollama -> Code Llama
```

## Important file: `without_rag.py`

This file is later used as the baseline for comparison. It asks Code Llama directly without retrieving information from the knowledge base.

```text
Question
   |
   v
Code Llama
   |
   v
Answer
```

---

# 8. Exercise 2 — Add a Knowledge Base

## Objective

Add application-specific knowledge that can later be retrieved.

The knowledge base contains:

```text
knowledge_base/
├── hpa_basics.txt
├── scaling_incidents.txt
└── scaling_policy.txt
```

These documents contain information about:

- Horizontal Pod Autoscaler concepts
- Reactive autoscaling delays
- Scaling incidents
- Scale-down behavior
- Capacity and bottlenecks

## Processing pipeline

```text
Documents
    |
    v
Chunking
    |
    v
Embeddings
    |
    v
Vector Representation
```

## Important file: `process_knowledge.py`

This file prepares the knowledge base.

It:

1. Reads the knowledge-base documents.
2. Splits them into chunks.
3. Generates embeddings using `nomic-embed-text`.
4. Stores the vector representations in ChromaDB.

The generated vector database is stored in:

```text
chroma_db/
```

## Why chunking?

A large document is divided into smaller pieces so retrieval can return the specific information relevant to a question.

```text
Document
   |
   +--- Chunk 1
   +--- Chunk 2
   +--- Chunk 3
```

---

# 9. Exercise 3 — Retrieval and RAG

## Objective

Add retrieval so the LLM can answer using relevant information from the knowledge base.

Retrieval:

```text
Question
   |
   v
Query Embedding
   |
   v
Vector Similarity
   |
   v
Relevant Chunks
   |
   v
Context
```

Generation:

```text
Context + Question
        |
        v
     Ollama
        |
        v
   Code Llama
        |
        v
     Answer
```

## Important file: `rag.py`

`rag.py`:

1. Accepts a question.
2. Creates a query embedding.
3. Searches ChromaDB.
4. Retrieves relevant chunks.
5. Builds context.
6. Sends context + question to Code Llama.
7. Prints the final answer.

## `rag.py` vs `without_rag.py`

Without RAG:

```text
Question
   |
   v
Code Llama
   |
   v
Answer
```

With RAG:

```text
Question
   |
   v
Embedding
   |
   v
Vector Search
   |
   v
Relevant Context
   |
   v
Code Llama
   |
   v
Answer
```

A useful demonstration question is:

```text
Why can reactive autoscaling be slow during a sudden traffic spike?
```

The RAG system can retrieve the knowledge-base explanation about detecting the load increase, calculating replicas, creating pods, and waiting for them to become ready.

---

# 10. Exercise 4 — APIs, Services and Orchestration

## Objective

Separate the application into logical services and make them communicate through APIs.

Final service layout:

```text
Application Service :8000
       |
       +----> RAG Service :8001
       |
       +----> LLM Service :8002
```

## `services/application_service.py`

This is the main orchestration service.

Endpoint:

```text
POST /ask
```

It:

1. Receives the user's question.
2. Calls the RAG service.
3. Receives relevant context.
4. Calls the LLM service with question + context.
5. Returns the final response.

It acts as the coordinator for one complete user request.

## `services/rag_service.py`

Endpoint:

```text
POST /retrieve
```

It:

1. Receives the question.
2. Creates the query embedding.
3. Searches ChromaDB.
4. Retrieves relevant chunks.
5. Returns context and source information.

The application service does not need to know how vector search is implemented internally.

## `services/llm_service.py`

Endpoint:

```text
POST /generate
```

It receives:

```json
{
  "question": "...",
  "context": "..."
}
```

and sends the information to:

```text
Ollama -> Code Llama
```

It then returns the generated response.

## Complete Exercise 4 request

```text
POST /ask
     |
     v
Application Service :8000
     |
     | POST /retrieve
     v
RAG Service :8001
     |
     v
Context
     |
     | POST /generate
     v
LLM Service :8002
     |
     v
Ollama -> Code Llama
     |
     v
Response
```

This demonstrates APIs, service separation, and orchestration.

---

# 11. Exercise 5 — Dockerization

## Objective

Containerize the relevant application services and demonstrate that they continue communicating.

The three services become Docker containers:

```text
application-service
rag-service
llm-service
```

Ollama remains on the Windows host.

---

## `Dockerfile.application`

Builds the Application Service image.

It:

1. Starts from Python 3.11.
2. Installs `requirements.txt`.
3. Copies the application service.
4. Exposes port 8000.
5. Starts Uvicorn.

## `Dockerfile.rag`

Builds the RAG Service image.

It:

1. Starts from Python 3.11.
2. Installs dependencies.
3. Copies the RAG service.
4. Includes the Chroma database.
5. Exposes port 8001.
6. Starts Uvicorn.

## `Dockerfile.llm`

Builds the LLM Service image.

It:

1. Starts from Python 3.11.
2. Installs dependencies.
3. Copies the LLM service.
4. Exposes port 8002.
5. Starts Uvicorn.

---

# 12. `docker-compose.yml`

Docker Compose creates and connects the three services.

Ports:

```text
Application -> 8000
RAG         -> 8001
LLM         -> 8002
```

Inside Docker, services communicate using service names:

```text
http://rag-service:8001
http://llm-service:8002
```

`127.0.0.1` must not be used to reach another container because inside a container `127.0.0.1` refers to that same container.

---

# 13. Docker → Windows Ollama

Ollama is running on the Windows host.

Containers access it using:

```text
http://host.docker.internal:11434
```

Therefore:

```text
RAG Container
     |
     v
host.docker.internal:11434
     |
     v
Windows Ollama
     |
     v
nomic-embed-text
```

and:

```text
LLM Container
     |
     v
host.docker.internal:11434
     |
     v
Windows Ollama
     |
     v
Code Llama
```

---

# 14. Running the Dockerized Application

Make sure Ollama is running:

```powershell
ollama list
```

Go to the project:

```powershell
cd "C:\coding\Devops assignment"
```

Build:

```powershell
docker compose build
```

Start:

```powershell
docker compose up
```

The services should listen on:

```text
Application: http://localhost:8000
RAG:         http://localhost:8001
LLM:         http://localhost:8002
```

---

# 15. Testing the Complete API

Open another PowerShell while Compose is running:

```powershell
$body = @{
    question = "Why can reactive autoscaling be slow during a sudden traffic spike?"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/ask" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

A successful request proves that the complete pipeline works.

Docker logs should show requests similar to:

```text
POST /retrieve 200 OK
POST /generate 200 OK
POST /ask 200 OK
```

---

# 16. Frontend

The project includes a simple browser UI:

```text
frontend/
├── index.html
├── style.css
└── script.js
```

The frontend is only the presentation layer.

It sends:

```text
POST http://127.0.0.1:8000/ask
```

It does not implement the RAG or LLM logic.

The backend remains:

```text
Application :8000
      |
      v
RAG :8001
      |
      v
LLM :8002
      |
      v
Ollama
```

## Running the frontend

Keep Docker Compose running:

```powershell
docker compose up
```

Then open `frontend/index.html` using VS Code Live Server.

Typical address:

```text
http://127.0.0.1:5500/frontend/
```

Ask a question through the browser UI.

---

# 17. Final Architecture

```text
                         USER
                           |
                           v
                 +------------------+
                 |    Frontend      |
                 |   HTML/CSS/JS    |
                 +--------+---------+
                          |
                          | HTTP
                          v
                 +------------------+
                 | Application      |
                 | Service :8000    |
                 +--------+---------+
                          |
                 +--------+--------+
                 |                 |
                 v                 v
        +----------------+  +----------------+
        | RAG Service    |  | LLM Service    |
        | :8001          |  | :8002          |
        +-------+--------+  +-------+--------+
                |                   |
                v                   |
          +-----------+             |
          | ChromaDB  |             |
          +-----------+             |
                |                   |
                +--------+----------+
                         |
                         v
                +----------------+
                | Ollama         |
                | Windows Host   |
                +-------+--------+
                        |
              +---------+---------+
              |                   |
              v                   v
      nomic-embed-text       Code Llama
              |                   |
              +---------+---------+
                        |
                        v
                     Answer
```

---

# 18. Exercise-by-Exercise Summary

## Exercise 1 — Basic LLM

**Goal:** Learn application-to-LLM communication.

```text
Application -> Ollama -> Code Llama
```

Main file:

```text
app.py
```

---

## Exercise 2 — Knowledge Base

**Goal:** Create application-specific knowledge.

```text
Documents
-> Chunking
-> Embeddings
-> Vector Representation
```

Main files:

```text
knowledge_base/*.txt
process_knowledge.py
```

Database:

```text
chroma_db/
```

Embedding model:

```text
nomic-embed-text
```

---

## Exercise 3 — RAG

**Goal:** Retrieve relevant information before generating an answer.

```text
Question
-> Query Embedding
-> Similarity Search
-> Relevant Context
-> Code Llama
```

Main files:

```text
rag.py
without_rag.py
```

---

## Exercise 4 — APIs & Services

**Goal:** Separate responsibilities into services.

```text
Application :8000
RAG         :8001
LLM         :8002
```

Main files:

```text
services/application_service.py
services/rag_service.py
services/llm_service.py
```

---

## Exercise 5 — Docker

**Goal:** Containerize the services and demonstrate that the complete system still works.

Main files:

```text
Dockerfile.application
Dockerfile.rag
Dockerfile.llm
docker-compose.yml
```

Final flow:

```text
Frontend
   |
Application
   |
RAG
   |
LLM
   |
Ollama
   |
Code Llama
```

---

# 19. Useful Commands

Check Ollama:

```powershell
ollama list
```

Check Docker:

```powershell
docker version
```

Check Docker Compose:

```powershell
docker compose version
```

Build:

```powershell
docker compose build
```

Start:

```powershell
docker compose up
```

Stop:

```powershell
docker compose down
```

Running containers:

```powershell
docker ps
```

All logs:

```powershell
docker compose logs
```

Application logs:

```powershell
docker compose logs application-service
```

RAG logs:

```powershell
docker compose logs rag-service
```

LLM logs:

```powershell
docker compose logs llm-service
```

---

# 20. Troubleshooting

## Docker daemon unavailable

Start Docker Desktop and run:

```powershell
docker version
```

Both `Client` and `Server` sections should appear.

## Ollama connection error

Check:

```powershell
ollama list
```

Then:

```powershell
Invoke-WebRequest http://localhost:11434/api/tags
```

From inside Docker, use:

```text
host.docker.internal:11434
```

not:

```text
127.0.0.1:11434
```

## `/ask` returns HTTP 500

Inspect each service:

```powershell
docker compose logs application-service --tail=50
docker compose logs rag-service --tail=50
docker compose logs llm-service --tail=50
```

This identifies which part of the chain failed.

---

# 21. What to Demonstrate During Evaluation

## Exercise 1

Show:

```text
User question
      ↓
Application
      ↓
Ollama
      ↓
Code Llama
      ↓
Response
```

## Exercise 2

Show:

```text
knowledge_base/
process_knowledge.py
chroma_db/
```

Explain:

> Documents are chunked, converted into embeddings using `nomic-embed-text`, and stored as vector representations in ChromaDB.

## Exercise 3

Ask the same question with and without RAG:

```text
Why can reactive autoscaling be slow during a sudden traffic spike?
```

Compare:

```text
without_rag.py
```

with:

```text
rag.py
```

Explain that RAG retrieves relevant knowledge before sending the context to Code Llama.

## Exercise 4

Show:

```text
Application :8000
RAG :8001
LLM :8002
```

Explain that the Application Service orchestrates the request by communicating with the RAG and LLM services through HTTP APIs.

## Exercise 5

Run:

```powershell
docker compose up
```

Show the containers running.

Then use the frontend to ask a question and show:

```text
Browser
   ↓
:8000
   ↓
:8001
   ↓
:8002
   ↓
Ollama
   ↓
Code Llama
   ↓
Response
```

This demonstrates that the complete application continues to work after containerization.

---

# 22. Complete Learning Progression

The assignment progressively transforms the system:

```text
Exercise 1
Basic LLM
      ↓
Exercise 2
Knowledge Base
      ↓
Exercise 3
RAG
      ↓
Exercise 4
APIs + Services + Orchestration
      ↓
Exercise 5
Dockerization
```

The final project combines:

**Frontend + FastAPI + RAG + ChromaDB + Ollama + Code Llama + Docker Compose**

into a complete local AI DevOps assistant.
