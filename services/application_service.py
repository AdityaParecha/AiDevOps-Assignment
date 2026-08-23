from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI(title="Application Service")
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


@app.post("/ask")
def ask_question(request: UserRequest):

    # Step 1: Ask RAG service for relevant context
    rag_response = requests.post(
        RAG_SERVICE_URL,
        json={
            "question": request.question,
            "n_results": 3
        }
    )

    rag_response.raise_for_status()

    rag_data = rag_response.json()

    context = rag_data["context"]
    sources = rag_data["sources"]

    # Step 2: Send question + retrieved context to LLM service
    llm_response = requests.post(
        LLM_SERVICE_URL,
        json={
            "question": request.question,
            "context": context
        }
    )

    llm_response.raise_for_status()

    llm_data = llm_response.json()

    # Step 3: Return final response
    return {
        "question": request.question,
        "answer": llm_data["response"],
        "sources": sources
    }