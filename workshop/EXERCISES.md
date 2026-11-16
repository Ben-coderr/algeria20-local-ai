# Workshop: Build & Deploy Local AI Apps (self-paced, ~2h)

| Lab | Topic | Time |
|---|---|---|
| 0 | Setup | 20 min |
| 1 | First local LLM + latency | 15 min |
| 2 | Prompting | 15 min |
| 3 | RAG on your documents | 30 min |
| 4 | Evaluate your RAG | 15 min |
| 5 | Build an agent | 30 min |
| 6 | Deploy with Docker | 20 min |

## Lab 0 — Setup
1. Install Ollama (ollama.com/download), Python 3.10+, optionally Docker.
2. `git clone <this repo> && cd algeria20-local-ai`
3. `python -m venv .venv`, activate it, `pip install -r requirements.txt`
4. `ollama pull llama3.2:3b`, `ollama pull bge-m3` (and `ollama pull qwen2.5:7b` for Lab 5)
5. Check: `ollama list` shows the models.

Only 8 GB RAM? Use a ~1B model: `CHAT_MODEL=llama3.2:1b`.

## Lab 1 — First local LLM
1. `ollama run llama3.2:3b` — ask 3 questions.
2. `python 01_hello.py "your question"` — note the first-token time and tokens/s.
3. Run it with a second model (`CHAT_MODEL=...`). Which is faster? Which answer is better?

## Lab 2 — Prompting
Edit the system prompt in `01_hello.py` and ask "What should I study to work in AI?":
- "Answer in exactly 3 bullet points."
- "Answer in Algerian Darija written in Latin letters."
- "You are a strict professor. Answer in one sentence."

Exercise: write a "study buddy" prompt that quizzes you instead of giving answers.

## Lab 3 — RAG on your own documents
1. Put 1–3 PDFs of your own course notes in `data/`.
2. `python rag_ingest.py`, then `python rag_ask.py` — ask 5 questions you know the answers to.
3. Check: answers cite the right source (page for PDFs, § section for Markdown).

Experiments (context management):
- `CHUNK_SIZE=300 python rag_ingest.py` then `CHUNK_SIZE=2000 ...` — better or worse? Why?
- `TOP_K=1` vs `TOP_K=8` — what changes? (More context ≠ better answers.)
- Ask something that is NOT in your documents. Does it say "I don't know"?

## Lab 4 — Evaluate
1. Open `eval_questions.json`. Replace it with 10 questions about YOUR documents (+ 2 whose answer is not there: `"expect": "UNKNOWN"`).
2. `python eval.py` — write down the score.
3. Change ONE thing (model, chunk size, TOP_K, system prompt). Run again. Keep the change only if the score improves.

## Lab 5 — Build an agent
1. `python agent.py` and read the "tool" lines.
2. Add your own tool, then add it to the `TOOLS` list:
```python
def dzd_to_eur(amount_dzd: float, rate: float = 150.0) -> str:
    """Convert Algerian dinars to euros.

    Args:
        amount_dzd: Amount in DZD.
        rate: How many DZD for 1 EUR (example value, not a live rate).

    Returns:
        Amount in EUR as text.
    """
    return f"{amount_dzd / rate:.2f} EUR"
```
3. Ask: "How much is the intern allowance in euros?"

Exercises: write a `read_file(path)` tool that can only read inside `data/` (block `..` — why?). Remove the docstrings — what happens?

## Lab 6 — Deploy
1. `docker compose up -d --build`
2. `docker compose exec ollama ollama pull llama3.2:3b` and `... bge-m3`
3. `docker compose exec app python rag_ingest.py`
4. Open http://localhost:8000 and http://localhost:8000/docs
5. Set `API_KEY=secret` in a `.env` file, restart, and check that `/ask` now returns 401 without the header.

## Bonus
Streaming UI · chat memory · PDF upload button · compare `EMBED_MODEL=nomic-embed-text` vs `bge-m3` on French/Arabic questions with `eval.py` · run a model with `transformers` or publish on a Hugging Face Space.

Share your result on LinkedIn with #Algeria20.
