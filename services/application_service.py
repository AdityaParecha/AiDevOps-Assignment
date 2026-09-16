import os
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from services.pipeline import DevOpsAssistantPipeline
from services.guardrails import GuardrailsPipeline, STANDARD_KB_REFUSAL

app = FastAPI(title="AI DevOps Scaling Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://rag-service:8001/retrieve")
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://llm-service:8002/generate")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "qwen2.5:3b")

pipeline = DevOpsAssistantPipeline()


class UserRequest(BaseModel):
    question: str
    model: str = DEFAULT_MODEL
    guardrails_enabled: bool = True


@app.get("/")
def root():
    return {
        "service": "Application Service",
        "status": "running",
        "guardrails_supported": True,
        "default_model": DEFAULT_MODEL
    }


@app.post("/ask")
def ask(request: UserRequest):
    question = request.question
    model = request.model or DEFAULT_MODEL
    guardrails_enabled = request.guardrails_enabled

    # If microservices are running in Docker, attempt them; otherwise use direct pipeline
    use_microservices = False
    if "rag-service" not in RAG_SERVICE_URL and "localhost" in RAG_SERVICE_URL:
        use_microservices = True

    if not use_microservices:
        # Use direct DevOpsAssistantPipeline (fast, local, fully guardrailed)
        res = pipeline.ask(
            question=question,
            model=model,
            guardrails_enabled=guardrails_enabled
        )
        return {
            "question": question,
            "answer": res["answer"],
            "raw_answer": res.get("raw_answer"),
            "model": model,
            "guardrails_applied": guardrails_enabled,
            "guardrail_status": res.get("guardrail_status"),
            "sources": res.get("sources", []),
            "prompt_tokens": res.get("prompt_tokens", 0),
            "output_tokens": res.get("output_tokens", 0),
            "total_tokens": res.get("total_tokens", 0),
            "generation_time_ms": res.get("generation_time_ms", 0),
            "latency_ms": res.get("latency_ms", 0)
        }

    # Microservices fallback path (if microservice URLs are explicitly targeted)
    guardrail_report: Dict[str, Any] = {
        "input": None,
        "retrieval": None,
        "output": None
    }

    if guardrails_enabled:
        input_decision = GuardrailsPipeline.process_input(question)
        guardrail_report["input"] = input_decision.to_dict()
        if not input_decision.passed:
            return {
                "question": question,
                "answer": input_decision.sanitized_content,
                "model": model,
                "guardrails_applied": True,
                "guardrail_status": guardrail_report,
                "sources": [],
                "prompt_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "generation_time_ms": 0
            }

    try:
        rag_response = requests.post(
            RAG_SERVICE_URL,
            json={"question": question, "n_results": 3},
            timeout=10
        )
        rag_response.raise_for_status()
        rag_data = rag_response.json()
        context = rag_data.get("context", "")
        sources = rag_data.get("sources", [])
        distances = [s.get("distance", 0.0) for s in sources]
    except Exception:
        # Fallback to local retrieval
        rag_data = pipeline.retrieve(question, n_results=3)
        context = rag_data["context"]
        sources = rag_data["sources"]
        distances = rag_data["distances"]

    if guardrails_enabled:
        retrieval_decision = GuardrailsPipeline.process_retrieval(
            question=question,
            context=context,
            distances=distances,
            sources=sources
        )
        guardrail_report["retrieval"] = retrieval_decision.to_dict()
        if not retrieval_decision.passed:
            return {
                "question": question,
                "answer": retrieval_decision.sanitized_content,
                "model": model,
                "guardrails_applied": True,
                "guardrail_status": guardrail_report,
                "sources": sources,
                "prompt_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "generation_time_ms": 0
            }

    llm_resp = pipeline.ollama_client.generate(
        model=model,
        prompt=f"Knowledge Base Context:\n{context}\n\nUser Question:\n{question}\n\nAnswer:"
    )
    raw_answer = llm_resp.get("response", "")

    final_answer = raw_answer
    if guardrails_enabled:
        output_decision = GuardrailsPipeline.process_output(
            question=question,
            context=context,
            raw_answer=raw_answer
        )
        guardrail_report["output"] = output_decision.to_dict()
        final_answer = output_decision.sanitized_content or raw_answer

    return {
        "question": question,
        "answer": final_answer,
        "raw_answer": raw_answer if guardrails_enabled else None,
        "model": model,
        "guardrails_applied": guardrails_enabled,
        "guardrail_status": guardrail_report if guardrails_enabled else None,
        "sources": sources,
        "prompt_tokens": llm_resp.get("prompt_eval_count", 0),
        "output_tokens": llm_resp.get("eval_count", 0),
        "total_tokens": llm_resp.get("prompt_eval_count", 0) + llm_resp.get("eval_count", 0),
        "generation_time_ms": llm_resp.get("eval_duration", 0) / 1_000_000
    }