from fastapi import FastAPI
from pydantic import BaseModel
import chromadb
import ollama
ollama_client = ollama.Client(
    host="http://host.docker.internal:11434"
)
app = FastAPI(title="RAG Service")


# Connect to existing Chroma database
client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_collection(
    name="devops_knowledge"
)


class RetrievalRequest(BaseModel):
    question: str
    n_results: int = 3


@app.post("/retrieve")
def retrieve(request: RetrievalRequest):

    # Convert question into embedding
    response = ollama_client.embed(
        model="nomic-embed-text",
        input=request.question
    )

    query_embedding = response["embeddings"][0]

    # Search vector database
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=request.n_results
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    context = "\n\n".join(documents)

    return {
        "context": context,
        "sources": [
            {
                "source": metadata["source"],
                "distance": distance
            }
            for metadata, distance in zip(metadatas, distances)
        ]
    }