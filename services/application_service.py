from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import requests

from pydantic import BaseModel


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


RAG_SERVICE_URL = "http://rag-service:8001/retrieve"
LLM_SERVICE_URL = "http://llm-service:8002/generate"


class UserRequest(BaseModel):
    question: str
    model: str = "qwen3.5:0.8b"


@app.get("/")
def root():
    return {
        "service": "Application Service",
        "status": "running"
    }


@app.post("/ask")
def ask(request: UserRequest):

    # -----------------------------
    # Step 1: Retrieve knowledge
    # -----------------------------

    rag_response = requests.post(
        RAG_SERVICE_URL,
        json={
            "question": request.question,
            "n_results": 3
        },
        timeout=120
    )

    rag_response.raise_for_status()

    rag_data = rag_response.json()

    context = rag_data.get("context", "")
    sources = rag_data.get("sources", [])


    # -----------------------------
    # Step 2: Generate answer
    # -----------------------------

    llm_response = requests.post(
        LLM_SERVICE_URL,
        json={
            "question": request.question,
            "context": context,
            "model": request.model
        },
        timeout=600
    )

    llm_response.raise_for_status()

    llm_data = llm_response.json()


    # -----------------------------
    # Step 3: Return complete result
    # -----------------------------

    return {
        "question": request.question,
        "answer": llm_data.get("response", ""),
        "model": llm_data.get("model", request.model),

        "sources": sources,

        "prompt_tokens": llm_data.get(
            "prompt_tokens",
            0
        ),

        "output_tokens": llm_data.get(
            "output_tokens",
            0
        ),

        "total_tokens": llm_data.get(
            "total_tokens",
            0
        ),

        "generation_time_ms": llm_data.get(
            "generation_time_ms",
            0
        )
    }