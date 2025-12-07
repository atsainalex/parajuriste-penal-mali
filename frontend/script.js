const API_URL = "http://127.0.0.1:8000/chat";

let currentMode = "public";
let conversationId = 1;
let history = [];

// ELEMENTS
const messagesEl = document.getElementById("messages");
const promptEl = document.getElementById("prompt");
const sendBtn = document.getElementById("send-btn");
const thinkingContainer = document.getElementById("thinking-container");
const historyListEl = document.getElementById("history-list");
const newChatBtn = document.getElementById("new-chat-btn");
const modeButtons = document.querySelectorAll(".mode-btn");
const themeToggle = document.getElementById("theme-toggle");

// AUTO-RESIZE TEXTAREA
promptEl.addEventListener("input", () => {
    promptEl.style.height = "auto";
    promptEl.style.height = promptEl.scrollHeight + "px";
});

// SEND ON ENTER (sans SHIFT)
promptEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

sendBtn.addEventListener("click", sendMessage);

// MODE SELECTION
modeButtons.forEach(btn => {
    btn.addEventListener("click", () => {
        modeButtons.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        currentMode = btn.dataset.mode || "public";
        addSystemMessage(`Mode changé : ${labelForMode(currentMode)}.`);
    });
});

// NOUVELLE DISCUSSION
newChatBtn.addEventListener("click", () => {
    conversationId += 1;
    history.push({ id: conversationId, title: `Discussion ${conversationId}` });
    renderHistory();
    messagesEl.innerHTML = "";
    addSystemMessage("Nouvelle discussion créée.");
});

// THEME TOGGLE (simple)
themeToggle.addEventListener("click", () => {
    document.body.classList.toggle("light");
});

// LABEL MODE
function labelForMode(mode) {
    switch (mode) {
        case "ong":
            return "ONG / Protection";
        case "magistrat":
            return "Magistrat";
        default:
            return "Grand public";
    }
}

// THINKING ANIMATION
function showThinking() {
    thinkingContainer.classList.remove("hidden");
}

function hideThinking() {
    thinkingContainer.classList.add("hidden");
}

// MESSAGE RENDERING
function addMessage(role, text) {
    const row = document.createElement("div");
    row.className = "message-row " + role;

    if (role === "assistant") {
        const avatar = document.createElement("div");
        avatar.className = "message-avatar";
        avatar.textContent = "⚖️";
        row.appendChild(avatar);
    }

    const bubble = document.createElement("div");
    bubble.className = "bubble";

    // On garde les sauts de ligne envoyés par le backend
    bubble.innerHTML = text
        .replace(/\n/g, "<br>");

    row.appendChild(bubble);
    messagesEl.appendChild(row);

    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function addSystemMessage(text) {
    const row = document.createElement("div");
    row.className = "message-row assistant";

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = "⚙️";
    row.appendChild(avatar);

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.style.opacity = "0.8";
    bubble.style.fontSize = "12px";
    bubble.innerHTML = text.replace(/\n/g, "<br>");

    row.appendChild(bubble);
    messagesEl.appendChild(row);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

// HISTORY RENDER
function renderHistory() {
    historyListEl.innerHTML = "";
    history.forEach(item => {
        const div = document.createElement("div");
        div.className = "history-item";
        div.textContent = item.title;
        historyListEl.appendChild(div);
    });
}

// INITIAL
history.push({ id: conversationId, title: "Discussion 1" });
renderHistory();
addSystemMessage("Bienvenue sur Parajuriste Pénal Mali. Pose ta première question.");

// MAIN SEND FUNCTION
async function sendMessage() {
    const text = promptEl.value.trim();
    if (!text) return;

    addMessage("user", text);
    promptEl.value = "";
    promptEl.style.height = "auto";

    showThinking();

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                prompt: text,
                mode: currentMode
            })
        });

        if (!response.ok) {
            hideThinking();
            addSystemMessage("Erreur de connexion au serveur backend.");
            return;
        }

        const data = await response.json();
        hideThinking();

        if (data.reply) {
            addMessage("assistant", data.reply);
        } else {
            addSystemMessage("Réponse vide reçue du backend.");
        }

    } catch (err) {
        hideThinking();
        addSystemMessage("Erreur réseau : " + err.message);
    }
}
