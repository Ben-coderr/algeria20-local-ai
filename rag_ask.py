"""Demo 2b: interactive Q&A in the terminal."""
import time

from rag import label, retrieve, stream_answer

print("Ask questions about your documents (type 'exit' to quit)\n")
while True:
    q = input("You: ").strip()
    if q.lower() in {"exit", "quit", ""}:
        break
    t0 = time.time()
    hits = retrieve(q)
    print("\nRetrieved:", " | ".join(dict.fromkeys(label(m) for _, m in hits)))
    print("Answer: ", end="")
    for token in stream_answer(q, hits):
        print(token, end="", flush=True)
    print(f"\n   [{time.time() - t0:.1f}s · 100% local]\n")
