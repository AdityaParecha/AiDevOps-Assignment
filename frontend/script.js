const API_URL = "http://127.0.0.1:8000/ask";

const form = document.getElementById("chatForm");
const input = document.getElementById("question");
const messages = document.getElementById("messages");

function addMessage(text, type) {
    const message = document.createElement("div");
    message.className = `message ${type}`;

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = text;

    message.appendChild(bubble);
    messages.appendChild(message);

    messages.scrollTop = messages.scrollHeight;
}

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const question = input.value.trim();

    if (!question) return;

    addMessage(question, "user");
    input.value = "";

    addMessage("Thinking...", "assistant");

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: question
            })
        });

        if (!response.ok) {
            throw new Error(`API returned ${response.status}`);
        }

        const data = await response.json();

        // Remove "Thinking..."
        messages.lastElementChild.remove();

        addMessage(data.answer, "assistant");

    } catch (error) {

        messages.lastElementChild.remove();

        addMessage(
            "Could not connect to the DevOps API. Make sure Docker Compose is running.",
            "assistant"
        );

        console.error(error);
    }
});