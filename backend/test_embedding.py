from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

resp = client.embeddings.create(
    model="text-embedding-3-large",
    input="Bonjour, ceci est un test d'embedding."
)

print("Embedding OK, longueur du vecteur :", len(resp.data[0].embedding))
