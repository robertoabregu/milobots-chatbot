from typing import List, Tuple
import os
import chromadb
from openai import OpenAI
from config import settings
from services.embeddings import embed_text
from services.prompts import SYSTEM_PERSONA, ANSWER_INSTRUCTIONS

# Inicializar cliente OpenAI
_client = None
def client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client

# Inicializar cliente Chroma (persistente en disco)
chroma_client = chromadb.PersistentClient(path="./vectorstore/chroma_db")
collection = chroma_client.get_or_create_collection("milobots")

def answer_with_rag(user_phone: str, question: str) -> Tuple[str, List[str]]:
    # Crear embedding de la pregunta
    q_vec = embed_text(question)

    # Buscar en Chroma top-k
    results = collection.query(
        query_embeddings=[q_vec],
        n_results=5
    )

    used_texts = results["documents"][0] if results["documents"] else []
    context = "\n\n".join([f"- {t}" for t in used_texts])

    messages = [
        {"role": "system", "content": SYSTEM_PERSONA},
        {"role": "user", "content": (
            f"{ANSWER_INSTRUCTIONS}\n\n"
            f"Contexto relevante:\n{context}\n\n"
            f"Usuario: {question}\n"
            f"Tu respuesta (sé útil, con voseo):"
        )},
    ]

    resp = client().chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=messages,
        temperature=0.6,
        max_tokens=600,
    )
    answer = resp.choices[0].message.content or "Perdón, no pude generar respuesta."
    return answer, used_texts
