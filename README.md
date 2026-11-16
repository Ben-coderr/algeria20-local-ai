# Algeria 2.0 — Build & Deploy AI Apps with Local, Open-Source Models

Companion repo for the Algeria 2.0 session *« Construire et Déployer des Applications IA en 2026 : Le Guide Pratique pour Développeurs & Étudiants »* (Wed 18 Nov 2026, Main Stage / Salle Conférence).
Everything runs on your laptop: no API key, no credit card, works offline.

## Start here (pick your level)
| You are… | Do this |
|---|---|
| **New to AI** | Open `docs/Local AI Field Guide.html` in your browser (English + العربية). Then install [Ollama](https://ollama.com/download) and run `ollama run llama3.2:3b`. |
| **Student / junior dev** | Follow the *Quick start* below, then do the labs in `workshop/EXERCISES.md`. |
| **Developer** | Read *What we measured* and *Production notes*, write your own eval questions, compare two models. |

**Homework from the talk:** build a RAG assistant for *your* course or club, post it on LinkedIn with **#Algeria20** and tag me: [linkedin.com/in/danour](https://www.linkedin.com/in/danour/).

## Use your own documents
1. Put your `.pdf`, `.md` or `.txt` files in `data/` (remove the sample handbook if you want).
2. `python rag_ingest.py` — cuts them into chunks and stores them in `chroma_db/`.
3. `python rag_ask.py` — ask questions; answers cite the file and page/section.
4. Write 10 questions you know the answers to in `eval_questions.json`, run `python eval.py`, and keep that score as your baseline.

## What's inside
| File | What it does |
|---|---|
| `01_hello.py` | Demo 1 — chat with a local LLM, prints first-token time, tokens/s |
| `rag_ingest.py`, `rag.py`, `rag_ask.py` | Demo 2 — local RAG (chat with your documents, EN / FR / AR) |
| `agent.py` | Demo 3 — agent that picks tools (search, calculator, notes) |
| `eval.py`, `eval_questions.json` | Evaluation — score your RAG, compare settings (`eval_results.log`) |
| `app.py` | Demo 4 — web UI (streaming) + REST API (`/ask`, `/ask/stream`, `/docs`) + optional API key |
| `Dockerfile`, `docker-compose.yml` | Deploy everything (app + Ollama) on a Linux server |
| `docker-compose.stage.yml` | App in Docker, Ollama on your laptop (Mac/Windows: faster, no double download) |
| `demo.sh` | Stage helper: `./demo.sh` lists the steps; each step prints the real command it runs |
| `workshop/EXERCISES.md` | Self-paced labs (~2 h) |
| `docs/Local AI Field Guide.html` | Beginner guide to every concept (EN / AR) |
| `backup/` | Real outputs of every demo, recorded on the talk laptop |
| `deck/` | Offline copy of the talk slides (served at `localhost:8000/deck/`) |

## Quick start
```bash
# 1. Install Ollama: https://ollama.com/download
ollama pull llama3.2:3b         # chat + RAG (fast)
ollama pull qwen2.5:7b          # agent (reliable tool calling)
ollama pull bge-m3              # multilingual embeddings (EN/FR/AR)

# 2. Python 3.10+
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Run
python 01_hello.py "Explain what an LLM is"
python rag_ingest.py && python rag_ask.py
python agent.py
python eval.py
uvicorn app:app --port 8000     # http://localhost:8000  and  /docs
```
Only 8 GB of RAM? `CHAT_MODEL=llama3.2:1b`, and try `AGENT_MODEL=qwen2.5:3b` (less reliable — measure it).
Model names change fast: check https://ollama.com/library.

## What we measured (Intel i5 laptop, 16 GB RAM, CPU only)
| Test | Result |
|---|---|
| `llama3.2:3b` chat | ~1 s to first word (warm), 9–14 tokens/s · cold start ~15 s |
| RAG answer (bge-m3 + llama3.2:3b) | ~3 s |
| Agent, `qwen2.5:3b` | 4/10 runs correct — skipped the calculator, wrong math |
| Agent, `qwen2.5:7b` | **10/10 runs correct**, ~25 s per task |
| Eval, bge-m3, top_k=4 | 12/12 in 82 s |
| Eval, bge-m3, top_k=1 | 12/12 in 55 s (less context → faster, same score) |
| Eval, nomic-embed-text (English-only), top_k=1 | 11/12 — the French question fails |

## Deploy
Linux server (everything in Docker):
```bash
docker compose up -d --build
docker compose exec ollama ollama pull llama3.2:3b
docker compose exec ollama ollama pull bge-m3
docker compose exec app python rag_ingest.py
```
Laptop (Ollama native, app in Docker): `docker compose -f docker-compose.stage.yml up -d --build`.
Public server: set `API_KEY` in `.env`, put Caddy/Nginx with HTTPS in front, never publish port 11434.

## Production notes
- Smaller model + good retrieval beats a bigger model alone. Always show sources. Prefer "I don't know" over inventing.
- Measure: first-token time, tokens/s, and an eval score after every change (`eval.py`). Change one thing at a time.
- Keep models warm (`keep_alive`), keep prompts short (`TOP_K`), cap the question length.
- Limit what agent tools can do (no `eval`, no shell, no unrestricted files). Documents can contain hostile instructions (prompt injection).
- Personal data? Respect Algerian Law 18-07; local hosting helps.
- Model licenses differ: check them before commercial use.

The sample handbook (Sahara Labs) is fictional.
