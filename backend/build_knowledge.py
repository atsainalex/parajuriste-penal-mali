import os
import json
import numpy as np
import faiss
from openai import OpenAI
from PyPDF2 import PdfReader

# ----------------------------
# CONFIG
# ----------------------------
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise RuntimeError("⚠️ OPENAI_API_KEY n'est pas défini dans l'environnement.")

client = OpenAI(api_key=API_KEY)

RAW_FOLDER = "knowledge/raw"
OUT_EMB = "knowledge/embeddings.npy"
OUT_FAISS = "knowledge/faiss.index"
OUT_PASSAGES = "knowledge/passages.json"

EMBED_MODEL = "text-embedding-3-large"

# ----------------------------
# UTILITAIRE LECTURE PDF
# ----------------------------
def extract_pdf_text(path):
    reader = PdfReader(path)
    full_text = ""
    for page in reader.pages:
        try:
            page_text = page.extract_text() or ""
            full_text += page_text + "\n"
        except:
            pass
    return full_text


# ----------------------------
# NETTOYAGE TEXTE
# ----------------------------
def clean_text(t):
    return (
        t.replace("\u0000", "")
         .replace("\ufb02", "fi")
         .replace("\ufb01", "fl")
         .replace("’", "'")
         .replace("“", '"')
         .replace("”", '"')
         .replace("•", "- ")
         .strip()
    )


# ----------------------------
# FRAGMENTATION EN CHUNKS
# ----------------------------
def chunk_text(text, source, max_size=800):
    words = text.split()
    chunks = []
    current = []

    for w in words:
        current.append(w)
        if len(current) >= max_size:
            chunks.append(" ".join(current))
            current = []

    if current:
        chunks.append(" ".join(current))

    return [{"source": source, "text": clean_text(c)} for c in chunks]


# ----------------------------
# EMBEDDING PAR BATCH
# ----------------------------
def embed_batch(list_of_texts, batch=50):
    embeddings = []

    for i in range(0, len(list_of_texts), batch):
        sub = list_of_texts[i:i + batch]

        print(f" → Embedding batch {i // batch + 1} / {(len(list_of_texts) - 1) // batch + 1}")

        resp = client.embeddings.create(
            model=EMBED_MODEL,
            input=sub
        )

        for e in resp.data:
            embeddings.append(e.embedding)

    return np.array(embeddings, dtype="float32")


# ----------------------------
# STEP 1 — EXTRACTION PDF
# ----------------------------
print("\n📘 Extraction des textes PDF…")

all_passages = []

for filename in os.listdir(RAW_FOLDER):
    if filename.lower().endswith(".pdf"):
        path = os.path.join(RAW_FOLDER, filename)
        print(f" • Lecture {filename}")

        raw = extract_pdf_text(path)
        chunks = chunk_text(raw, source=filename)
        all_passages.extend(chunks)

print(f"✔ TOTAL CHUNKS : {len(all_passages)}")


# ----------------------------
# STEP 2 — ENREGISTREMENT passages.json
# ----------------------------
with open(OUT_PASSAGES, "w", encoding="utf-8") as f:
    json.dump(all_passages, f, indent=2, ensure_ascii=False)

print(f"✔ FICHIER SAUVÉ : {OUT_PASSAGES}")


# ----------------------------
# STEP 3 — EMBEDDING
# ----------------------------
print("\n🧠 Génération des embeddings…")

all_texts = [p["text"] for p in all_passages]
embeddings = embed_batch(all_texts, batch=40)

np.save(OUT_EMB, embeddings)

print(f"✔ EMBEDDINGS SAUVÉS : {OUT_EMB}")
print(f"   → taille : {embeddings.shape}")


# ----------------------------
# STEP 4 — CRÉATION FAISS INDEX
# ----------------------------
print("\n📂 Construction du FAISS index…")

dim = embeddings.shape[1]
index = faiss.IndexFlatL2(dim)
index.add(embeddings)

faiss.write_index(index, OUT_FAISS)

print(f"✔ INDEX FAISS SAUVÉ : {OUT_FAISS}")
print("\n🎉 Base de connaissance générée avec succès !")
