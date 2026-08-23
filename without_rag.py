import ollama

question = input("Question: ")

response = ollama.generate(
    model="codellama",
    prompt=question,
    stream=False
)

print("\n========== WITHOUT RAG ==========\n")
print(response["response"])