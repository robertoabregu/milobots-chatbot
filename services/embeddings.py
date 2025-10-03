from typing import List
from openai import OpenAI
from config import settings

_client = None

def client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client

def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Retorna embeddings para una lista de textos usando OpenAI.
    """
    if not texts:
        return []
    resp = client().embeddings.create(
        input=texts,
        model=settings.OPENAI_EMBEDDING_MODEL,
    )
    return [d.embedding for d in resp.data]

def embed_text(text: str) -> List[float]:
    return embed_texts([text])[0]
