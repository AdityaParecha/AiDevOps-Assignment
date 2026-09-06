import ollama

from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI()


ollama_client = ollama.Client(
    host="http://host.docker.internal:11434"
)


class LLMRequest(BaseModel):
    question: str
    context: str
    model: str


@app.get("/")
def root():
    return {
        "service": "LLM Service",
        "status": "running"
    }


@app.post("/generate")
def generate(request: LLMRequest):

    prompt = f"""
You are an AI DevOps Scaling Assistant.

Answer the user's question using the provided knowledge base context.

IMPORTANT RULES:
1. Use the context as the primary source of truth.
2. Do not invent facts that are not present in the context.
3. If the context does not contain enough information to answer,
   clearly say that the information is not available.
4. Give a concise but useful technical answer.

Knowledge Base Context:
{request.context}

User Question:
{request.question}

Answer:
"""

    response = ollama_client.generate(
        model=request.model,
        prompt=prompt
    )

    prompt_tokens = response.get("prompt_eval_count", 0)
    output_tokens = response.get("eval_count", 0)
    total_tokens = prompt_tokens + output_tokens

    generation_time_ns = response.get("eval_duration", 0)

    generation_time_ms = (
        generation_time_ns / 1_000_000
        if generation_time_ns
        else 0
    )

    return {
        "response": response.get("response", ""),
        "model": request.model,
        "prompt_tokens": prompt_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "generation_time_ms": generation_time_ms
    }