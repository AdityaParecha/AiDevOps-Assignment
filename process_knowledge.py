import os
import chromadb
import ollama

KNOWLEDGE_DIR = "knowledge_base"

# Create a local Chroma database
client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(
    name="devops_knowledge"
)


def chunk_text(text, chunk_size=500, overlap=50):
    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def create_embedding(text):
    response = ollama.embed(
        model="nomic-embed-text",
        input=text
    )

    return response["embeddings"][0]


def process_documents():

    document_count = 0
    chunk_count = 0

    for filename in os.listdir(KNOWLEDGE_DIR):

        if not filename.endswith(".txt"):
            continue

        filepath = os.path.join(KNOWLEDGE_DIR, filename)

        with open(filepath, "r", encoding="utf-8") as file:
            text = file.read()

        chunks = chunk_text(text)

        print(f"\nProcessing: {filename}")
        print(f"Chunks created: {len(chunks)}")

        for i, chunk in enumerate(chunks):

            embedding = create_embedding(chunk)

            collection.add(
                ids=[f"{filename}_{i}"],
                documents=[chunk],
                embeddings=[embedding],
                metadatas=[{"source": filename}]
            )

            chunk_count += 1

        document_count += 1

    print("\n==============================")
    print("Knowledge Base Created")
    print("==============================")
    print(f"Documents processed: {document_count}")
    print(f"Chunks stored: {chunk_count}")


if __name__ == "__main__":
    process_documents()