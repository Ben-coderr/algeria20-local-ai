#!/usr/bin/env bash
# Stage helper — every step prints the REAL command, then runs it.
# Usage:  ./demo.sh <step>        (run ./demo.sh with no argument to see the list)
set -u
cd "$(dirname "$0")"
[ -d .venv ] && source .venv/bin/activate
export PYTHONWARNINGS=ignore

G=$'\e[1;32m'; Y=$'\e[1;33m'; R=$'\e[1;31m'; D=$'\e[2m'; N=$'\e[0m'
show() { printf "\n${G}\$ %s${N}\n\n" "$*"; }
run()  { show "$*"; eval "$@"; }
title(){ printf "\n${Y}━━━ %s ━━━${N}\n" "$*"; }

case "${1:-}" in

  check)   # Pre-flight: run 30-60 min before the talk, then again 10 min before.
    title "PRE-FLIGHT CHECK"
    ok=1
    curl -s -m 3 localhost:11434/api/version >/dev/null && echo "[ok] Ollama is running" || { echo "${R}[FAIL] Ollama is not running → open the Ollama app${N}"; ok=0; }
    for m in llama3.2:3b qwen2.5:7b bge-m3 nomic-embed-text; do
      ollama list | grep -q "^$m" && echo "[ok] model $m" || { echo "${R}[FAIL] missing $m → ollama pull $m (at home, not at the venue)${N}"; ok=0; }
    done
    [ -d chroma_db ] && echo "[ok] RAG index (chroma_db/)" || { echo "${Y}… building RAG index${N}"; python rag_ingest.py >/dev/null && echo "[ok] RAG index built"; }
    [ -d chroma_nomic ] && echo "[ok] 'bad config' index for the eval demo" || { echo "${Y}… building eval comparison index${N}"; EMBED_MODEL=nomic-embed-text DB_PATH=chroma_nomic python rag_ingest.py >/dev/null && echo "[ok] comparison index built"; }
    free=$(df -g . | awk 'NR==2{print $4}')
    [ "$free" -ge 10 ] && echo "[ok] disk free: ${free} GB" || echo "${Y}[warn] disk free: ${free} GB (keep ≥10 GB so macOS can swap)${N}"
    curl -s -m 3 localhost:8000/health >/dev/null && echo "[ok] web app on http://localhost:8000" || echo "${Y}[warn] web app not running → ./demo.sh web (in a 2nd terminal tab)${N}"
    rm -f notes.md && echo "[ok] notes.md cleared (agent demo starts clean)"
    [ $ok = 1 ] && echo "${G}READY.${N} Now run: ./demo.sh warmup" || echo "${R}FIX THE [FAIL] LINES FIRST.${N}"
    ;;

  warmup)  # Load all models in RAM for 2 hours. Run ~10 min before going on stage.
    title "WARM-UP (loads models into memory — takes 1-2 min the first time)"
    for m in llama3.2:3b qwen2.5:7b; do
      printf "  %-14s" "$m"; s=$(date +%s)
      curl -s localhost:11434/api/generate -d "{\"model\":\"$m\",\"prompt\":\"hi\",\"keep_alive\":\"2h\",\"options\":{\"num_predict\":1}}" >/dev/null
      echo "loaded in $(( $(date +%s) - s ))s"
    done
    # Only 3 models: Ollama keeps max 3 in memory by default. nomic-embed-text is used
    # only by "eval-bad" (after the agent demo) and loads in ~2 s.
    for m in bge-m3; do
      printf "  %-14s" "$m"; s=$(date +%s)
      curl -s localhost:11434/api/embed -d "{\"model\":\"$m\",\"input\":\"hi\",\"keep_alive\":\"2h\"}" >/dev/null
      echo "loaded in $(( $(date +%s) - s ))s"
    done
    ollama ps
    ;;

  slides)  # The deck is served by the web app (./demo.sh web must be running). Works offline.
    open "http://localhost:8000/deck/" ;;

  models)  run "ollama list" ;;

  hello)   # Demo 1
    title "DEMO 1 — a local LLM"
    run "python 01_hello.py \"Give me 3 AI project ideas for Algerian students, one line each.\""
    ;;

  hallucinate)  # Demo 1 → RAG bridge: same question, different invented answers
    title "DEMO 1b — ask the same question 3 times"
    for i in 1 2 3; do run "python 01_hello.py \"Explain RAG in one sentence\" | head -1"; done
    ;;

  ingest)  title "DEMO 2 — index the documents"; run "python rag_ingest.py" ;;
  rag)     title "DEMO 2 — chat with the documents"; run "python rag_ask.py" ;;

  eval)    # Demo 2b — the good configuration, 5 questions (~25 s)
    title "EVAL — good config (multilingual embeddings)"
    run "python eval.py --quick"
    ;;

  eval-bad)  # Same test, English-only embeddings + 1 chunk: the French question breaks
    title "EVAL — change ONE thing: English-only embeddings"
    run "EMBED_MODEL=nomic-embed-text DB_PATH=chroma_nomic TOP_K=1 python eval.py --quick"
    ;;

  agent)   rm -f notes.md; title "DEMO 3 — an agent with tools"; run "python agent.py"; run "cat notes.md" ;;
  agent2)  title "DEMO 3b"; run "python agent.py \"How much does an intern earn during the whole internship?\"" ;;

  web)     # Demo 4 (and the opening hook). Keep it running in its own terminal tab.
    title "DEMO 4 — web app on http://localhost:8000"
    run "uvicorn app:app --port 8000"
    ;;

  api)     # Demo 4 — call the API like any other program would
    run "curl -s localhost:8000/ask -H 'Content-Type: application/json' -d '{\"question\":\"What is the remote work day?\"}' | python -m json.tool --no-ensure-ascii"
    ;;

  docker)  # Demo 4 — the same app, packaged
    title "DEMO 4 — deploy with Docker"
    run "cat docker-compose.yml"
    run "docker compose -f docker-compose.stage.yml ps"
    ;;

  security)  # Demo 4 — with an API key, strangers get 401
    title "SECURITY — API key ON (app on port 8001)"
    API_KEY=algeria20 uvicorn app:app --port 8001 >/dev/null 2>&1 & pid=$!; sleep 3
    run "curl -s -o /dev/null -w 'without key → HTTP %{http_code}\n' localhost:8001/ask -H 'Content-Type: application/json' -d '{\"question\":\"hi\"}'"
    run "curl -s -o /dev/null -w 'with key    → HTTP %{http_code}\n' localhost:8001/ask -H 'Content-Type: application/json' -H 'X-API-Key: algeria20' -d '{\"question\":\"What is the remote work day?\"}'"
    kill $pid 2>/dev/null
    ;;

  *)
    cat <<EOF
${Y}Stage helper${N}   ./demo.sh <step>

  ${G}check${N}        pre-flight checks (do it 30 min before)
  ${G}warmup${N}       load all models in memory (10 min before)
  ${G}slides${N}       open the deck: http://localhost:8000/deck/  (needs ./demo.sh web)
  ${G}hello${N}        Demo 1  · local LLM + latency
  ${G}hallucinate${N}  Demo 1b · same question 3×, 3 invented answers
  ${G}ingest${N}       Demo 2  · index documents
  ${G}rag${N}          Demo 2  · ask questions (EN / FR / AR / "CEO?")
  ${G}agent${N}        Demo 3  · agent: search → calculator → save note
  ${G}agent2${N}       Demo 3b · second agent task (optional)
  ${G}eval${N}         Eval    · 5 test questions, good config   (AFTER the agent)
  ${G}eval-bad${N}     Eval    · English-only embeddings → French fails
  ${G}web${N}          Demo 4  · start web app (own terminal tab)
  ${G}api${N}          Demo 4  · call the API with curl
  ${G}docker${N}       Demo 4  · show compose file + running containers
  ${G}security${N}     Demo 4  · API key: 401 vs 200
EOF
    ;;
esac
