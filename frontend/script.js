// Dynamic API Host (supports localhost or 127.0.0.1 seamlessly)
const API_HOST = window.location.hostname || "127.0.0.1";
const API_URL = `http://${API_HOST}:8000/ask`;
const HEALTH_URL = `http://${API_HOST}:8000/`;

const form = document.getElementById("chatForm");
const input = document.getElementById("question");
const messages = document.getElementById("messages");
const sendButton = document.getElementById("sendButton");
const sendText = document.getElementById("sendText");
const spinner = document.getElementById("spinner");
const guardrailsToggle = document.getElementById("guardrailsToggle");
const guardrailLabel = document.getElementById("guardrailLabel");
const apiPill = document.querySelector(".api-pill");

// 1. Initial Health Check
async function checkBackendHealth() {
    try {
        const res = await fetch(HEALTH_URL, { method: "GET", signal: AbortSignal.timeout(3000) });
        if (res.ok) {
            if (apiPill) {
                apiPill.innerHTML = '<span class="pulse" style="background:#48bb78"></span> API Connected (:8000)';
                apiPill.style.borderColor = "#48bb78";
            }
        }
    } catch (e) {
        if (apiPill) {
            apiPill.innerHTML = '<span class="pulse" style="background:#f56565"></span> API Offline (:8000)';
            apiPill.style.borderColor = "#f56565";
        }
    }
}
checkBackendHealth();

// 2. Toggle Guardrail UI label
if (guardrailsToggle && guardrailLabel) {
    guardrailsToggle.addEventListener("change", () => {
        if (guardrailsToggle.checked) {
            guardrailLabel.textContent = "Guardrails ON";
            guardrailLabel.style.color = "#68d391";
        } else {
            guardrailLabel.textContent = "Guardrails OFF";
            guardrailLabel.style.color = "#fc8181";
        }
    });
}

// 3. Handle Enter Key (Enter sends, Shift+Enter makes newline)
if (input) {
    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            form.dispatchEvent(new Event("submit"));
        }
    });
}

// 4. Bind Quick Suggestion Buttons
document.querySelectorAll(".suggestions button").forEach((btn) => {
    btn.addEventListener("click", () => {
        const q = btn.getAttribute("data-question");
        if (q && input) {
            input.value = q;
            form.dispatchEvent(new Event("submit"));
        }
    });
});

// 5. Add Chat Message to DOM
function addMessage(text, type, guardrailMeta = null) {
    // Hide welcome box on first chat message
    const welcome = document.querySelector(".welcome");
    if (welcome && welcome.style.display !== "none") {
        welcome.style.display = "none";
    }

    const message = document.createElement("div");
    message.className = `message ${type}`;

    const bubble = document.createElement("div");
    bubble.className = "bubble";

    if (guardrailMeta) {
        const badge = document.createElement("div");
        badge.style.fontSize = "11px";
        badge.style.fontWeight = "600";
        badge.style.letterSpacing = "0.03em";
        badge.style.padding = "4px 9px";
        badge.style.borderRadius = "6px";
        badge.style.display = "inline-block";
        badge.style.marginBottom = "10px";

        if (guardrailMeta.action === "BLOCK") {
            badge.style.color = "#c53030";
            badge.style.background = "#fff5f5";
            badge.style.border = "1px solid #feb2b2";
            const gName = guardrailMeta.guardrail === "InputScopeGuardrail" 
                ? "Scope Guardrail (Out of Domain)" 
                : guardrailMeta.guardrail;
            badge.textContent = `🛡️ ${gName}`;
        } else if (guardrailMeta.action === "ALLOW") {
            badge.style.color = "#22543d";
            badge.style.background = "#f0fff4";
            badge.style.border = "1px solid #9ae6b4";
            badge.textContent = `🛡️ Guardrail: Grounded Response`;
        }
        bubble.appendChild(badge);
    }

    const textNode = document.createElement("div");
    textNode.style.whiteSpace = "pre-wrap";
    textNode.textContent = text;
    bubble.appendChild(textNode);

    message.appendChild(bubble);
    messages.appendChild(message);

    messages.scrollTop = messages.scrollHeight;
}

// 6. Form Submission Handler
form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const question = input.value.trim();
    if (!question) return;

    // Display user bubble
    addMessage(question, "user");
    input.value = "";
    input.style.height = "auto";

    // Show loading state
    if (sendButton) sendButton.disabled = true;
    if (sendText) sendText.textContent = "...";
    if (spinner) spinner.classList.remove("hidden");

    addMessage("Thinking...", "assistant");

    const guardrailsEnabled = guardrailsToggle ? guardrailsToggle.checked : true;

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: question,
                guardrails_enabled: guardrailsEnabled
            })
        });

        if (!response.ok) {
            throw new Error(`API returned HTTP ${response.status}`);
        }

        const data = await response.json();

        // Remove "Thinking..." bubble
        if (messages.lastElementChild) {
            messages.lastElementChild.remove();
        }

        // Determine which guardrail metadata to display
        let guardrailMeta = null;
        if (data.guardrails_applied && data.guardrail_status) {
            const st = data.guardrail_status;
            if (st.input && !st.input.passed) {
                guardrailMeta = st.input;
            } else if (st.retrieval && !st.retrieval.passed) {
                guardrailMeta = st.retrieval;
            } else if (st.output && !st.output.passed) {
                guardrailMeta = st.output;
            } else {
                guardrailMeta = { action: "ALLOW", guardrail: "All Stages Validated" };
            }
        }

        addMessage(data.answer, "assistant", guardrailMeta);

    } catch (error) {
        if (messages.lastElementChild) {
            messages.lastElementChild.remove();
        }
        addMessage(
            "⚠️ Could not connect to API on port 8000. Please ensure the backend service is running:\n" +
            "python3 -m uvicorn services.application_service:app --host 127.0.0.1 --port 8000",
            "assistant"
        );
        console.error("Chat API error:", error);
    } finally {
        if (sendButton) sendButton.disabled = false;
        if (sendText) sendText.textContent = "Ask";
        if (spinner) spinner.classList.add("hidden");
        input.focus();
    }
});