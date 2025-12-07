const API_URL = "https://parajuriste-penal-mali-backend…/chat"; // garde ton URL actuelle

let currentMode = "public";
let conversationId = 1;
let history = [];

// ÉLÉMENTS
const messagesEl = document.getElementById("messages");
const promptEl = document.getElementById("prompt");
const sendBtn = document.getElementById("send-btn");
const thinkingContainer = document.getElementById("thinking-container");

// (l’historique complet n’est pas encore visible dans cette UI, mais on garde la logique)
let historyListEl = document.getElementById("history-list");
let newChatBtn = document.getElementById("new-chat-btn");
let modeButtons = document.querySelectorAll(".mode-btn");
let themeToggle = document.getElementById("theme-toggle");

// Certains éléments peuvent être absents dans ce design : on sécurise
if (!historyListEl) {
  historyListEl = { innerHTML: "" };
}
if (!newChatBtn) {
  newChatBtn = { addEventListener: () => {} };
}
if (!modeButtons || modeButtons.length === 0) {
  modeButtons = [];
}
if (!themeToggle) {
  themeToggle = { addEventListener: () => {} };
}

// AUTO-RESIZE TEXTAREA
promptEl.addEventListener("input", () => {
  promptEl.style.height = "auto";
  promptEl.style.height = promptEl.scrollHeight + "px";
});

// ENVOI SUR ENTER (sans Shift)
promptEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

sendBtn.addEventListener("click", sendMessage);

// SÉLECTION MODE (si boutons présents)
modeButtons.forEach(btn => {
  btn.addEventListener("click", () => {
    modeButtons.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentMode = btn.dataset.mode || "public";
    addSystemMessage(`Mode changé : ${labelForMode(currentMode)}.`);
  });
});

// NOUVELLE DISCUSSION (si bouton présent)
newChatBtn.addEventListener("click", () => {
  conversationId += 1;
  history.push({ id: conversationId, title: `Discussion ${conversationId}` });
  renderHistory();
  messagesEl.innerHTML = "";
  addSystemMessage("Nouvelle discussion créée.");
});

// THEME (si toggle présent)
themeToggle.addEventListener("click", () => {
  document.body.classList.toggle("light");
});

// LABEL MODE
function labelForMode(mode) {
  switch (mode) {
    case "ong": return "ONG / Protection";
    case "magistrat": return "Magistrat";
    default: return "Grand public";
  }
}

// ANIMATION "PENSE"
function showThinking() {
  if (thinkingContainer) thinkingContainer.classList.remove("hidden");
}
function hideThinking() {
  if (thinkingContainer) thinkingContainer.classList.add("hidden");
}

/* -------- FORMATAGE DES TEXTES -------- */

/**
 * Met en gras les références d’articles de loi
 * Exemple : Article 45 du Code pénal
 */
function boldLawArticles(text) {
  return text.replace(
    /(Article\s+\d+[A-Za-z0-9\/\-]*\s+du\s+Code[^.\n]*)/gi,
    "<strong>$1</strong>"
  );
}

/**
 * Aère le texte : remplace les sauts de ligne par <br><br>
 */
function addSpacing(text) {
  return text.replace(/\n+/g, "<br><br>");
}

/**
 * Formatage complet d’une réponse IA
 */
function formatAssistantText(raw) {
  let t = raw;
  t = boldLawArticles(t);
  t = addSpacing(t);
  return t;
}

/* -------- AFFICHAGE DES MESSAGES -------- */

function addMessage(role, text) {
  const row = document.createElement("div");
  row.className = "message-row " + role;

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";

  if (role === "assistant") {
    bubble.innerHTML = formatAssistantText(text);
  } else {
    // utilisateur : on garde les retours à la ligne simples
    bubble.innerHTML = text.replace(/\n/g, "<br>");
  }

  row.appendChild(bubble);
  messagesEl.appendChild(row);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function addSystemMessage(text) {
  const row = document.createElement("div");
  row.className = "message-row assistant";

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  bubble.style.background = "#e5e7eb";
  bubble.style.fontSize = "12px";
  bubble.style.color = "#4b5563";
  bubble.innerHTML = text.replace(/\n/g, "<br>");

  row.appendChild(bubble);
  messagesEl.appendChild(row);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

/* -------- HISTORIQUE (LOGIQUE SIMPLE) -------- */

function renderHistory() {
  if (!historyListEl || !historyListEl.innerHTML) return;
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
addSystemMessage(
  "Bienvenue sur Parajuriste Pénal Mali. Pose ta première question en droit pénal ou de procédure pénale."
);

/* -------- ENVOI AU BACKEND -------- */

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
