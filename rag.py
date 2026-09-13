import chromadb
import ollama

# --------------------------------------------------
# Ollama configuration
# --------------------------------------------------

OLLAMA_HOST = "http://127.0.0.1:11434"

ollama_client = ollama.Client(host=OLLAMA_HOST)


# --------------------------------------------------
# Connect to existing Chroma database
# --------------------------------------------------

client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_collection(
    name="devops_knowledge"
)


# --------------------------------------------------
# Retrieve relevant context from Chroma
# --------------------------------------------------

def retrieve_context(question, n_results=3):

    # Generate embedding for the question
    response = ollama_client.embed(
        model="nomic-embed-text:latest",
        input=question
    )

    query_embedding = response["embeddings"][0]

    # Search Chroma
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )

    documents = results["documents"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]

    return documents, distances, metadatas


# --------------------------------------------------
# Main
# --------------------------------------------------

if __name__ == "__main__":

    question = input("Question: ")

    try:

        # Retrieve relevant documents
        documents, distances, metadatas = retrieve_context(question)

        # Combine retrieved documents
        context = "\n\n".join(documents)

        # Build RAG prompt
        prompt = f"""
You are an AI DevOps Scaling Assistant.

Answer the user's question using ONLY the provided context.

If the answer is not present in the context, say:

"The provided knowledge base does not contain enough information."

Do not make up information.

Context:
{context}

User Question:
{question}

Answer:
"""

        # Generate answer
        response = ollama_client.generate(
            model="mistral:latest",
            prompt=prompt,
            stream=False
        )

        print("\n========== RAG RESPONSE ==========\n")
        print(response["response"])

    except Exception as e:

        print("\n========== ERROR ==========\n")
        print(e)