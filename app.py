import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "codellama"


def ask_llm(question):
    payload = {
        "model": MODEL,
        "prompt": question,
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload)
    response.raise_for_status()

    return response.json()["response"]


while True:
    question = input("\nYou: ")

    if question.lower() == "exit":
        print("Goodbye!")
        break

    answer = ask_llm(question)

    print("\nCode Llama:")
    print(answer)