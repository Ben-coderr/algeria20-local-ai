import os
from ollama import Client

# Change models / settings here or with environment variables.
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
CHAT_MODEL = os.getenv("CHAT_MODEL", "llama3.2:3b")
AGENT_MODEL = os.getenv("AGENT_MODEL", "qwen2.5:7b")
# bge-m3 is multilingual (French / Arabic / English questions on the same docs).
# nomic-embed-text is smaller but English-first. Compare both with eval.py.
EMBED_MODEL = os.getenv("EMBED_MODEL", "bge-m3")

DB_PATH = os.getenv("DB_PATH", "chroma_db")
COLLECTION = "docs"

# Context-management knobs ("context" slide + workshop Lab 3)
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
TOP_K = int(os.getenv("TOP_K", "4"))

# Keep models in memory between demos. Ollama's default is 5 minutes:
# without this, a model goes cold in the middle of a talk and the next call
# waits several seconds to reload it from disk.
KEEP_ALIVE = os.getenv("KEEP_ALIVE", "2h")

# Low temperature = more repeatable answers (important for demos and evals).
OPTIONS = {"temperature": float(os.getenv("TEMPERATURE", "0.2"))}

client = Client(host=OLLAMA_HOST)
