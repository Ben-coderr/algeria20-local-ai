"""Mini evaluation: run test questions, score the answers.

Usage:  python eval.py                 (all questions in eval_questions.json)
        python eval.py --quick         (first 5 questions: fast enough for a live demo)
Compare settings:  TOP_K=1 python eval.py      CHAT_MODEL=qwen2.5:3b python eval.py

Every run is appended to eval_results.log so you can compare settings later.
"""
import datetime
import json
import pathlib
import sys
import time

from config import CHAT_MODEL, EMBED_MODEL, TOP_K, CHUNK_SIZE
from rag import answer

UNKNOWN_MARKERS = ("don't know", "do not know", "لا أعرف", "لا أعلم")


def norm(s: str) -> str:
    return (s.lower().replace(",", "").replace(".", "").replace(" ", "")
            .replace(" ", "").replace(" ", "").replace("’", "'"))


def is_ok(expect: str, text: str) -> bool:
    if expect == "UNKNOWN":
        return any(norm(m) in norm(text) for m in UNKNOWN_MARKERS)
    return norm(expect) in norm(text)


def main():
    cases = json.loads(pathlib.Path("eval_questions.json").read_text(encoding="utf-8"))
    if "--quick" in sys.argv:
        cases = [c for c in cases if c.get("quick")]
    passed, t0 = 0, time.time()
    for c in cases:
        text, _ = answer(c["q"])
        ok = is_ok(c["expect"], text)
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  {c['q']}")
        if not ok:
            print(f"     expected: {c['expect']!r} | got: {text[:120]!r}")
    n = len(cases)
    line = (f"Score: {passed}/{n} = {100 * passed / n:.0f}%  "
            f"[chat={CHAT_MODEL} embed={EMBED_MODEL} k={TOP_K} chunk={CHUNK_SIZE} | {time.time() - t0:.0f}s]")
    print("\n" + line)
    with open("eval_results.log", "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now():%Y-%m-%d %H:%M}  {line}\n")


if __name__ == "__main__":
    main()
