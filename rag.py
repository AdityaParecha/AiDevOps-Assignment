import chromadb
import ollama

# Connect to our existing Chroma database
client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_collection(
    name="devops_knowledge"
)


def retrieve_context(question, n_results=3):

    # Convert the user's question into an embedding
    response = ollama.embed(
        model="nomic-embed-text",
        input=question
    )

    query_embedding = response["embeddings"][0]

    # Search Chroma for similar chunks
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )

    documents = results["documents"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]

    return documents, distances, metadatas


if __name__ == "__main__":

    question = input("Question: ")

    documents, distances, metadatas = retrieve_context(question)

    context = "\n\n".join(documents)

    prompt = f"""
You are an AI DevOps Scaling Assistant.

Answer the user's question using the provided context.

If the answer is not present in the context, say that the
provided knowledge base does not contain enough information.

Context:
{context}

User Question:
{question}

Answer:
"""

    response = ollama.generate(
        model="codellama",
        prompt=prompt,
        stream=False
    )

    print("\n========== RAG RESPONSE ==========\n")
    print(response["response"])