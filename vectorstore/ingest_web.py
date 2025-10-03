import argparse, os, json, re, requests
from bs4 import BeautifulSoup
from readability import Document
from services.embeddings import embed_texts
import faiss, numpy as np
from config import settings

def extract_text_from_url(url: str) -> str:
    html = requests.get(url, timeout=20).text
    doc = Document(html)
    summary_html = doc.summary()
    soup = BeautifulSoup(summary_html, "html.parser")
    txt = soup.get_text("\n")
    txt = re.sub(r"\n{2,}", "\n", txt).strip()
    return txt

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

def main(url: str):
    txt = extract_text_from_url(url)
    chunks = chunk_text(txt, chunk_size=700, overlap=120)
    vecs = embed_texts(chunks)
    dim = len(vecs[0])
    index = faiss.IndexFlatIP(dim)
    index.add(np.array(vecs).astype("float32"))
    os.makedirs(os.path.dirname(settings.VECTORSTORE_PATH), exist_ok=True)
    faiss.write_index(index, settings.VECTORSTORE_PATH)
    meta = [(url, c) for c in chunks]
    with open(settings.VECTORSTORE_PATH + ".meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)
    print(f"OK: {len(chunks)} chunks de {url} -> {settings.VECTORSTORE_PATH}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    args = ap.parse_args()
    main(args.url)
