"""RAG core: retrieve relevant chunks, build the prompt, answer from them only."""
import chromadb

from config import client, CHAT_MODEL, EMBED_MODEL, DB_PATH, COLLECTION, TOP_K, KEEP_ALIVE, OPTIONS

SYSTEM_PROMPT = """You are a helpful assistant that answers ONLY from the provided context.
Rules:
- Answer in the same language as the question (English question -> English answer, Arabic question -> Arabic answer).
- If the answer is not in the context, do not guess. Say only:
  "I don't know based on these documents." (if the question is in Arabic: "لا أعرف بناءً على هذه الوثائق.")
- Be short and clear: one or two sentences.
- Cite the source exactly as written in the context header, e.g. [sahara_labs_handbook.md § Leave]. Never invent a page."""

_collection = None


def collection():
    global _collection
    if _collection is None:
        _collection = chromadb.PersistentClient(path=DB_PATH).get_collection(COLLECTION)
    return _collection


def retrieve(question: str, k: int = TOP_K):
    """Return a list of (text, metadata) most similar to the question."""
    q_emb = client.embed(model=EMBED_MODEL, input=question, keep_alive=KEEP_ALIVE)["embeddings"][0]
    res = collection().query(query_embeddings=[q_emb], n_results=k)
    return list(zip(res["documents"][0], res["metadatas"][0]))


def label(m) -> str:
    """Human-readable source, e.g. 'handbook.md § Leave' or 'course.pdf p.3'."""
    return f"{m['source']} {m.get('loc', '')}".strip()


def build_messages(question: str, hits):
    context = "\n\n".join(f"[{label(m)}]\n{doc}" for doc, m in hits)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
    ]


def answer(question: str, k: int = TOP_K):
    """Non-streaming answer. Returns (answer_text, hits)."""
    hits = retrieve(question, k)
    resp = client.chat(model=CHAT_MODEL, messages=build_messages(question, hits),
                       keep_alive=KEEP_ALIVE, options=OPTIONS)
    return resp["message"]["content"], hits


def stream_answer(question: str, hits):
    """Yield answer tokens one by one (used by rag_ask.py and the web app)."""
    for chunk in client.chat(model=CHAT_MODEL, messages=build_messages(question, hits),
                             stream=True, keep_alive=KEEP_ALIVE, options=OPTIONS):
        yield chunk["message"]["content"]
