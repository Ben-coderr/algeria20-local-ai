"""Demo 4: web API + simple UI.

Run:  uvicorn app:app --port 8000      then open http://localhost:8000  (API docs: /docs)
Optional protection: set API_KEY to require an X-API-Key header on /ask and /ask/stream.
"""
import json
import os
import time

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from config import CHAT_MODEL, EMBED_MODEL
from rag import answer, label, retrieve, stream_answer

API_KEY = os.getenv("API_KEY")  # empty = open (fine for local demo, NOT for the internet)

app = FastAPI(title="Algeria 2.0 — Local RAG Assistant")

# The talk's slides, served offline at http://localhost:8000/deck/
if os.path.isdir("deck"):
    app.mount("/deck", StaticFiles(directory="deck", html=True), name="deck")


class Question(BaseModel):
    # A length limit is a cheap protection against abuse (huge prompts = slow, costly calls).
    question: str = Field(min_length=1, max_length=500)


def check_key(x_api_key: str | None = Header(default=None)):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


def sources_of(hits):
    return list(dict.fromkeys(label(m) for _, m in hits))  # keep relevance order


@app.get("/health")
def health():
    return {"status": "ok", "chat_model": CHAT_MODEL, "embed_model": EMBED_MODEL}


@app.post("/ask", dependencies=[Depends(check_key)])
def ask(q: Question):
    t0 = time.time()
    text, hits = answer(q.question)
    return {"answer": text, "sources": sources_of(hits), "seconds": round(time.time() - t0, 1)}


@app.post("/ask/stream", dependencies=[Depends(check_key)])
def ask_stream(q: Question):
    """Streams newline-delimited JSON: sources first, then tokens, then timing."""
    def events():
        t0 = time.time()
        hits = retrieve(q.question)
        yield json.dumps({"sources": sources_of(hits)}) + "\n"
        first = None
        for token in stream_answer(q.question, hits):
            if first is None:
                first = time.time() - t0
            yield json.dumps({"token": token}) + "\n"
        yield json.dumps({"done": True, "first": round(first or 0, 1),
                          "total": round(time.time() - t0, 1)}) + "\n"
    return StreamingResponse(events(), media_type="application/x-ndjson")


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Local AI Assistant</title>
<style>
 :root{--green:#3f8f17;--green-soft:#eaf5e2;--ink:#14210d;--muted:#5b6655;--line:#d8e2d0;--orange:#e8730c}
 *{box-sizing:border-box}
 body{font-family:-apple-system,system-ui,"Segoe UI",Roboto,sans-serif;margin:0;background:#fbfcf9;color:var(--ink)}
 main{max-width:900px;margin:0 auto;padding:40px 24px 60px}
 header{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap}
 h1{font-size:44px;margin:0;letter-spacing:-.02em} h1 span{color:var(--green)}
 .badges{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0 28px}
 .badge{font-size:17px;padding:6px 12px;border-radius:99px;background:var(--green-soft);color:var(--green);font-weight:600}
 .badge.o{background:#fdf0e3;color:var(--orange)}
 form{display:flex;gap:10px}
 input{flex:1;min-width:0;padding:18px 20px;font-size:26px;border:3px solid var(--green);border-radius:14px;outline:none;background:#fff}
 button{padding:0 28px;font-size:24px;font-weight:700;background:var(--green);color:#fff;border:0;border-radius:14px;cursor:pointer}
 button:disabled{opacity:.5}
 .chips{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}
 .chip{font-size:17px;padding:8px 14px;border:1.5px solid var(--line);border-radius:99px;background:#fff;color:var(--muted);cursor:pointer}
 .chip:hover{border-color:var(--green);color:var(--green)}
 #card{margin-top:30px;padding:28px;border-radius:18px;background:#fff;border:1.5px solid var(--line);display:none}
 #out{font-size:30px;line-height:1.45;white-space:pre-wrap;min-height:44px}
 #src{margin-top:18px;font-size:19px;color:var(--muted)} #src b{color:var(--green)}
 #meta{margin-top:8px;font-size:17px;color:var(--muted);font-variant-numeric:tabular-nums}
 .cursor::after{content:"▍";color:var(--green);animation:b 1s steps(1) infinite}@keyframes b{50%{opacity:0}}
 footer{margin-top:40px;font-size:15px;color:var(--muted)}
</style></head><body><main>
<header><h1>Local AI <span>Assistant</span></h1></header>
<div class="badges"><span class="badge">100% open-source</span><span class="badge">runs on this laptop</span>
<span class="badge">no API key · no card</span><span class="badge o" id="models">…</span></div>
<form id="f"><input id="q" placeholder="Ask about the documents… / اسأل عن الوثائق…" autocomplete="off" autofocus>
<button id="go">Ask</button></form>
<div class="chips">
 <span class="chip">How many leave days do full-time employees get?</span>
 <span class="chip" dir="rtl">كم يوم عطلة يحصل عليها الموظف؟</span>
 <span class="chip">Who is the CEO of Sahara Labs?</span>
</div>
<div id="card"><div id="out"></div><div id="src"></div><div id="meta"></div></div>
<footer>Algeria 2.0 · Demo · Ollama + Chroma + FastAPI · sample data: fictional Sahara Labs handbook</footer>
</main>
<script>
const $=id=>document.getElementById(id);
fetch('/health').then(r=>r.json()).then(d=>{$('models').textContent=d.chat_model+' · '+d.embed_model}).catch(()=>{});
document.querySelectorAll('.chip').forEach(c=>c.onclick=()=>{$('q').value=c.textContent;ask()});
$('f').onsubmit=e=>{e.preventDefault();ask()};
async function ask(){
  const q=$('q').value.trim(); if(!q) return;
  const out=$('out'); $('card').style.display='block'; $('go').disabled=true;
  out.textContent='Searching the documents…'; out.className='cursor'; $('src').textContent=''; $('meta').textContent='';
  try{
    const r=await fetch('/ask/stream',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q})});
    if(!r.ok){out.className='';out.textContent=r.status===401?'401 — API key required (security is ON)':'Error '+r.status;return;}
    const reader=r.body.getReader(), dec=new TextDecoder(); let buf='', started=false;
    for(;;){
      const {value,done}=await reader.read(); if(done) break;
      buf+=dec.decode(value,{stream:true}); const lines=buf.split('\\n'); buf=lines.pop();
      for(const l of lines){ if(!l.trim()) continue; const d=JSON.parse(l);
        if(d.sources){ $('src').innerHTML='<b>Retrieved (best first):</b> '; $('src').append(d.sources.join(', ')); out.textContent='Thinking…'; }
        if(d.token!==undefined){ if(!started){out.textContent='';started=true;} out.textContent+=d.token; }
        if(d.done){ $('meta').textContent='⏱ first word '+d.first+'s · total '+d.total+'s · cost 0 DA'; }
      }
    }
  }catch(e){ out.textContent='Could not reach the server.'; }
  finally{ out.className=''; $('go').disabled=false; }
}
</script></body></html>"""


@app.get("/", response_class=HTMLResponse)
def home():
    return PAGE
