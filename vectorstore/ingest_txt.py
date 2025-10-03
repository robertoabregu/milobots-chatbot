import argparse, os
import chromadb
from services.embeddings import embed_texts
from config import settings

def chunk_text(text: str, chunk_size=900, overlap=150):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i:i+chunk_size]
        chunks.append(" ".join(chunk))
        i += chunk_size - overlap
        if i <= 0:
            break
    return chunks

def main(input_path: str):
    if not os.path.exists(input_path):
        raise FileNotFoundError(input_path)
    with open(input_path, "r", encoding="utf-8") as f:
        txt = f.read()

    chunks = chunk_text(txt, chunk_size=700, overlap=120)
    vecs = embed_texts(chunks)

    chroma_client = chromadb.PersistentClient(path="./vectorstore/chroma_db")
    collection = chroma_client.get_or_create_collection("milobots")

    # Limpiar y volver a cargar
    collection.delete(where={})
    for i, (chunk, vec) in enumerate(zip(chunks, vecs)):
        collection.add(
            ids=[f"chunk_{i}"],
            documents=[chunk],
            embeddings=[vec]
        )

    print(f"OK: {len(chunks)} chunks guardados en Chroma")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Ruta del .txt a vectorizar")
    args = ap.parse_args()
    main(args.input)
