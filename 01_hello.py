"""Demo 1: talk to a local LLM, and measure latency.

Usage:
    python 01_hello.py "your question"
    CHAT_MODEL=qwen2.5:3b python 01_hello.py "your question"   # compare models
"""
import sys
import time

from config import client, CHAT_MODEL, KEEP_ALIVE, OPTIONS

question = " ".join(sys.argv[1:]) or "Explain what an LLM is in two sentences, for a first-year student."

start = time.time()
first_token = None
final = None
for chunk in client.chat(
    model=CHAT_MODEL,
    messages=[
        {"role": "system", "content": "You are a concise, friendly teacher. Keep answers under 80 words."},
        {"role": "user", "content": question},
    ],
    stream=True,
    keep_alive=KEEP_ALIVE,
    options=OPTIONS,
):
    if first_token is None:
        first_token = time.time() - start
    print(chunk["message"]["content"], end="", flush=True)
    final = chunk

total = time.time() - start
# Ollama reports exact token counts in the last chunk.
out_tokens = getattr(final, "eval_count", None) or 0
gen_seconds = (getattr(final, "eval_duration", None) or 0) / 1e9
speed = out_tokens / gen_seconds if gen_seconds else 0
print(
    f"\n\n[{CHAT_MODEL} | first token {first_token:.1f}s | total {total:.1f}s | "
    f"{out_tokens} tokens · {speed:.0f} tokens/s | cost 0 DA | 100% local]"
)
