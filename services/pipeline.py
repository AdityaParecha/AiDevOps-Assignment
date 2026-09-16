"""
Core Pipeline Orchestrator for AI DevOps Scaling Assistant
==========================================================

Provides local and service-based execution for RAG queries with full
support for toggling guardrails ON and OFF.

Used by:
- FastAPI Application Service
- Demonstration scripts (demo_guardrails.py)
- Quantitative evaluation scripts (test_guardrails.py)
- AI Output Testing framework (run_output_tests.py)
"""

import os
import time
from typing import Dict, Any, List, Optional
import chromadb
import ollama

from services.guardrails import GuardrailsPipeline, STANDARD_KB_REFUSAL


OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "qwen2.5:3b")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")


class DevOpsAssistantPipeline:
    """
    Executes the complete query lifecycle:
      [Input Guardrail] -> [ChromaDB Retrieval] -> [Retrieval Guardrail]
      -> [LLM Generation] -> [Output Guardrail]
    """

    def __init__(self, chroma_path: str = CHROMA_PATH, ollama_host: str = OLLAMA_HOST):
        self.chroma_path = chroma_path
        self.ollama_client = ollama.Client(host=ollama_host)
        self._chroma_client = None
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            self._chroma_client = chromadb.PersistentClient(path=self.chroma_path)
            self._collection = self._chroma_client.get_collection(name="devops_knowledge")
        return self._collection

    def retrieve(self, question: str, n_results: int = 3) -> Dict[str, Any]:
        """Queries ChromaDB using nomic-embed-text embeddings."""
        embed_resp = self.ollama_client.embed(
            model=EMBEDDING_MODEL,
            input=question
        )
        query_embedding = embed_resp["embeddings"][0]

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        documents = results["documents"][0] if results["documents"] else []
        metadatas = results["metadatas"][0] if results["metadatas"] else []
        distances = results["distances"][0] if results["distances"] else []

        sources = [
            {"source": meta.get("source", "unknown"), "distance": dist}
            for meta, dist in zip(metadatas, distances)
        ]

        context = "\n\n".join(documents)
        return {
            "context": context,
            "documents": documents,
            "distances": distances,
            "sources": sources
        }

    def ask(
        self,
        question: str,
        model: str = DEFAULT_MODEL,
        guardrails_enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Executes a question through the pipeline.
        If guardrails_enabled=True: applies multi-stage guardrails.
        If guardrails_enabled=False: runs raw unconstrained pipeline to demonstrate
        unprotected failure modes.
        """
        start_time = time.perf_counter()
        guardrail_status: Dict[str, Any] = {
            "input": None,
            "retrieval": None,
            "output": None
        }

        # ----------------------------------------------------
        # 1. INPUT GUARDRAIL
        # ----------------------------------------------------
        if guardrails_enabled:
            input_decision = GuardrailsPipeline.process_input(question)
            guardrail_status["input"] = input_decision.to_dict()

            if not input_decision.passed:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                return {
                    "question": question,
                    "answer": input_decision.sanitized_content,
                    "raw_answer": None,
                    "model": model,
                    "guardrails_applied": True,
                    "guardrail_status": guardrail_status,
                    "sources": [],
                    "context": "",
                    "distances": [],
                    "prompt_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "latency_ms": elapsed_ms
                }

        # ----------------------------------------------------
        # 2. RETRIEVE CONTEXT
        # ----------------------------------------------------
        rag_data = self.retrieve(question, n_results=3)
        context = rag_data["context"]
        sources = rag_data["sources"]
        distances = rag_data["distances"]

        # ----------------------------------------------------
        # 3. RETRIEVAL GUARDRAIL
        # ----------------------------------------------------
        if guardrails_enabled:
            retrieval_decision = GuardrailsPipeline.process_retrieval(
                question=question,
                context=context,
                distances=distances,
                sources=sources
            )
            guardrail_status["retrieval"] = retrieval_decision.to_dict()

            if not retrieval_decision.passed:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                return {
                    "question": question,
                    "answer": retrieval_decision.sanitized_content,
                    "raw_answer": None,
                    "model": model,
                    "guardrails_applied": True,
                    "guardrail_status": guardrail_status,
                    "sources": sources,
                    "context": context,
                    "distances": distances,
                    "prompt_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "latency_ms": elapsed_ms
                }

        # ----------------------------------------------------
        # 4. LLM GENERATION
        # ----------------------------------------------------
        if guardrails_enabled:
            # Strictly constrained RAG prompt enforcing groundedness
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
{context}

User Question:
{question}

Answer:
"""
        else:
            # Unguarded prompt: no strict refusal or security boundaries
            # Demonstrates raw, uncontrolled LLM behavior (answers off-topic, attempts injections, hallucinates)
            prompt = f"""You are a helpful AI assistant.

Knowledge Base Context (if any):
{context}

User Question:
{question}

Answer:
"""
        gen_start = time.perf_counter()
        llm_resp = self.ollama_client.generate(
            model=model,
            prompt=prompt
        )
        gen_time_ms = (time.perf_counter() - gen_start) * 1000

        raw_answer = llm_resp.get("response", "")
        prompt_tokens = llm_resp.get("prompt_eval_count", 0)
        output_tokens = llm_resp.get("eval_count", 0)
        total_tokens = prompt_tokens + output_tokens

        # ----------------------------------------------------
        # 5. OUTPUT GUARDRAIL
        # ----------------------------------------------------
        final_answer = raw_answer
        if guardrails_enabled:
            output_decision = GuardrailsPipeline.process_output(
                question=question,
                context=context,
                raw_answer=raw_answer
            )
            guardrail_status["output"] = output_decision.to_dict()
            final_answer = output_decision.sanitized_content or raw_answer

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return {
            "question": question,
            "answer": final_answer,
            "raw_answer": raw_answer if guardrails_enabled else None,
            "model": model,
            "guardrails_applied": guardrails_enabled,
            "guardrail_status": guardrail_status if guardrails_enabled else None,
            "sources": sources,
            "context": context,
            "distances": distances,
            "prompt_tokens": prompt_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "generation_time_ms": gen_time_ms,
            "latency_ms": elapsed_ms
        }
