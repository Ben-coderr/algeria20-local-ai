"""Demo 2a: index documents (.pdf / .md / .txt) into a local Chroma database."""
import pathlib
import sys

import chromadb
from pypdf import PdfReader

from config import client, EMBED_MODEL, DB_PATH, COLLECTION, CHUNK_SIZE, CHUNK_OVERLAP, KEEP_ALIVE

SUPPORTED = {".pdf", ".md", ".txt"}


def load_pages(path: pathlib.Path):
    """Return a list of (location, text). location = page number (PDF) or section title (Markdown)."""
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(path)
        return [(f"p.{i + 1}", page.extract_text() or "") for i, page in enumerate(reader.pages)]
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".md":
        # One piece per "## Section": cleaner chunks and readable sources ("§ Leave").
        sections, title, lines = [], "intro", []
        for line in text.splitlines():
            if line.startswith("## "):
                if "".join(lines).strip():
                    sections.append((f"§ {title}", "\n".join(lines)))
                title, lines = line[3:].strip(), [line]
            else:
                lines.append(line)
        if "".join(lines).strip():
            sections.append((f"§ {title}", "\n".join(lines)))
        return sections
    return [("p.1", text)]


def chunk(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    """Split text into overlapping pieces so ideas aren't cut in half."""
    if overlap >= size:
        raise ValueError("overlap must be smaller than size")
    pieces, start = [], 0
    while start < len(text):
        pieces.append(text[start:start + size])
        start += size - overlap
    return [p for p in pieces if p.strip()]


def main(folder: str = "data"):
    db = chromadb.PersistentClient(path=DB_PATH)
    try:
        db.delete_collection(COLLECTION)  # start fresh each time
    except Exception:
        pass
    col = db.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})

    files = sorted(f for f in pathlib.Path(folder).iterdir() if f.suffix.lower() in SUPPORTED)
    total = 0
    for f in files:
        for i_loc, (loc, text) in enumerate(load_pages(f)):
            pieces = chunk(text)
            if not pieces:
                continue
            embeddings = client.embed(model=EMBED_MODEL, input=pieces, keep_alive=KEEP_ALIVE)["embeddings"]
            col.add(
                ids=[f"{f.name}-{i_loc}-c{i}" for i in range(len(pieces))],
                documents=pieces,
                embeddings=embeddings,
                metadatas=[{"source": f.name, "loc": loc}] * len(pieces),
            )
            total += len(pieces)
        print(f"indexed {f.name}")
    print(f"\nDone: {total} chunks stored in '{DB_PATH}/' (embed={EMBED_MODEL}, chunk={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data")
