import os
import json
import faiss
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI

# -------------------------
# CONFIG
# -------------------------
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

EMBED_MODEL = "text-embedding-3-large"
CHAT_MODEL = "gpt-4.1"

# -------------------------
# CHARGEMENT BASE DE CONNAISSANCE
# -------------------------
FAISS_PATH = "knowledge/faiss.index"
EMB_PATH = "knowledge/embeddings.npy"
PASS_PATH = "knowledge/passages.json"

if not os.path.exists(FAISS_PATH):
    print("[INFO] ⚠️ Aucune base vectorielle trouvée — réponses sans contexte.")
    FAISS = None
    PASSAGES = []
else:
    print("[INFO] Base de connaissance FAISS chargée.")
    FAISS = faiss.read_index(FAISS_PATH)
    EMBEDDINGS = np.load(EMB_PATH)
    with open(PASS_PATH, "r", encoding="utf-8") as f:
        PASSAGES = json.load(f)

# -------------------------
# FASTAPI
# -------------------------
app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)

@app.options("/chat")
async def preflight_handler():
    return {}

class Query(BaseModel):
    prompt: str
    mode: str = "public"


# -------------------------
# EMBEDDING
# -------------------------
def embed_text(text: str):
    r = client.embeddings.create(
        model=EMBED_MODEL,
        input=text
    )
    return np.array(r.data[0].embedding, dtype="float32")


# -------------------------
# RECHERCHE DANS FAISS
# -------------------------
def search_knowledge(query: str, k: int = 5):
    if FAISS is None:
        return []

    q_emb = embed_text(query).reshape(1, -1)
    _, idx = FAISS.search(q_emb, k)

    results = []
    for i in idx[0]:
        if i < len(PASSAGES):
            results.append(PASSAGES[i]["text"])
    return results


# -------------------------
# FORMATAGE DE LA RÉPONSE (10px entre lignes)
# -------------------------
def format_final_answer(text: str) -> str:
    """
    Règles obligatoires de réponse :
    - Tu dois toujours mettre en gras toute référence à un article de loi.
    - Tu dois aérer la réponse avec un saut de ligne entre chaque catégorie de réponse.
    - Tu dois expliquer clairement avant de citer la loi.
    - Tu termines toujours par un conseil pratique.
    - Nettoie les mauvaises citations
    """

    if not text:
        return text

    # 1. Interdiction des guides citoyens
    forbidden = [
        "Guide Citoyen du Code pénal",
        "Guide citoyen du Code pénal",
        "Guide Citoyen du Code de procédure pénale",
        "Guide citoyen du Code de procédure pénale",
        "guide citoyen",
        "Guide citoyen"
    ]
    for f in forbidden:
        text = text.replace(f, "")

    # 2. Découper par phrases avec regex
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text)

    result = ""
    for s in sentences:
        if s.strip():
            result += s.strip() + "<br><div style='margin-bottom:10px;'></div>"

    # Nettoyage
    while "<br><div style='margin-bottom:10px;'></div><br>" in result:
        result = result.replace(
            "<br><div style='margin-bottom:10px;'></div><br>",
            "<br><div style='margin-bottom:10px;'></div>"
        )

    return result.strip()


# -------------------------
# PROMPT STRICT ZÉRO HALLUCINATION
# -------------------------
def build_prompt(user_prompt: str, mode: str, context_blocks: list):

    context_text = "\n\n".join(f"- {c}" for c in context_blocks)

    return f"""
Tu es Parajuriste Pénal Mali, un assistant juridique spécialisé en droit pénal et procédure pénale du Mali.

Tu dois toujours répondre selon cette structure stricte :

1. 🟢 Réponse directe : une phrase claire.
2. 📘 L’explication simple : en langage accessible avec des puces.
3. ⚖️ La preuve juridique : uniquement Constitution (2023), Code pénal (2024) ou Code de procédure pénale (2024). Les articles doivent être en **gras**.
4. 💡 Conseil pratique : actions immédiates à faire.
5. ⚠️ Avertissement : 
"Je suis ton assistant juridique virtuel. Je suis là pour t’expliquer la loi et t’aider dans tes démarches. Pour la suite de la procédure au tribunal, l’assistance d’un avocat ou d’une association reste conseillée."

Règles obligatoires :
- Toute référence juridique doit être en **gras**.
- La réponse doit être très aérée.
- Le langage doit être simple.
- Aucune référence aux guides citoyens.
- Tu dois toujours raisonner avec le droit malien exclusivement.

Fourni plus de détails quand tu donnes des réponses aux question qu'on te pose, soit empathique tout en étant professionnel en repondant, réagit comme un Avocat conseil.

🛑 **RÈGLE ABSOLUE :**
Tu dois répondre UNIQUEMENT avec les extraits ci-dessous provenant :
- du Code pénal 2024
- du Code de procédure pénale 2024
- de la Constitution 2023
- des documents fournis dans la base vectorielle

Cite aussi les sources des articles provenant des documents :
- du Code pénal 2024
- du Code de procédure pénale 2024
- de la Constitution 2023

Précise de quels documents proviennent les articles que tu cites.

Met en gras tous les articles que tu cites

Règles obligatoires de réponse :
- Tu dois toujours mettre en **gras** toute référence à un article de loi.
- Tu dois aérer la réponse avec un saut de ligne entre chaque catégorie de réponse.
- Tu dois expliquer simplement avant de citer la loi.
- Tu termines toujours par un conseil pratique.

Si un article ou une règle ne figure PAS dans les extraits FAISS, tu écris :
"Je ne trouve pas cet article dans la base de connaissances fournie."

---

📚 **EXTRAITS DISPONIBLES :**
{context_text}

---

🎯 **FORMAT OBLIGATOIRE DE LA RÉPONSE :**
ne revient pas à la ligne après chaque point, supprime les ** et met les articles et sources que tu cites en gras

1. 🟢 Réponse directe  
2. 📘 Explication simple  
3. ⚖️ Preuve juridique  
4. 💡 Conseil pratique  
5. ⚠️ Avertissement  

---

❓ **QUESTION :**
{user_prompt}
"""


# -------------------------
# ROUTE PRINCIPALE /chat
# -------------------------
@app.post("/chat")
def chat(q: Query):

    mode = q.mode
    question = q.prompt

    # 1. Recherche dans la base locale
    context = search_knowledge(question)

    # 2. Construction du prompt final
    final_prompt = build_prompt(question, mode, context)

    # 3. Appel OpenAI
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": "Tu es Parajuriste Pénal Mali, assistant strict, zéro hallucination."},
            {"role": "user", "content": final_prompt}
        ]
    )

    raw_answer = response.choices[0].message.content

    # 4. Formatage HTML avec espacement 10px
    formatted = format_final_answer(raw_answer)

    # 5. Réponse propre
    return {
        "reply": formatted,
        "mode": mode,
        "sources": context
    }
