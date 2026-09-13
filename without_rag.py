import ollama

# Connect to local Ollama server
ollama_client = ollama.Client(
    host="http://127.0.0.1:11434"
)

question = input("Question: ")

try:
    response = ollama_client.generate(
        model="mistral:latest",
        prompt=question,
        stream=False
    )

    print("\n========== WITHOUT RAG ==========\n")
    print(response["response"])

except Exception as e:
    print("\n========== ERROR ==========\n")
    print(e)
