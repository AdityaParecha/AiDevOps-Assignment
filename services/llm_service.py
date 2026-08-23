from fastapi import FastAPI
from pydantic import BaseModel
import ollama

ollama_client = ollama.Client(
    host="http://host.docker.internal:11434"
)
app = FastAPI(title="LLM Service")


class LLMRequest(BaseModel):
    question: str
    context: str


@app.post("/generate")
def generate_response(request: LLMRequest):

    prompt = f"""
You are an AI DevOps Scaling Assistant.

Answer the user's question using the provided context.

If the answer is not present in the context, say that the
provided knowledge base does not contain enough information.

Context:
{request.context}

User Question:
{request.question}

Answer:
"""

    response = ollama_client.generate(
        model="codellama",
        prompt=prompt,
        stream=False
    )

    return {
        "response": response["response"]
    }