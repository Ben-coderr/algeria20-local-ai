"""Demo 3: an agent that decides which tools to call."""
import ast
import datetime
import operator
import sys
import time

from config import client, AGENT_MODEL, KEEP_ALIVE, OPTIONS
from rag import label, retrieve

# ---------- Tools ----------
# The docstrings matter: the model reads them to decide which tool to use.

_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Mod: operator.mod, ast.USub: operator.neg,
}  # no Pow: 9**9**9 could freeze the agent


def _safe_eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("Only basic arithmetic is allowed")


def calculator(expression: str) -> str:
    """Calculate a math expression such as '24 - (7 + 5)' or '6 * 40000'.

    Args:
        expression: An arithmetic expression using numbers, + - * / % and parentheses.

    Returns:
        The result as text.
    """
    try:
        return str(_safe_eval(ast.parse(expression, mode="eval").body))
    except Exception as e:
        return f"Error: {e}"


def search_documents(query: str) -> str:
    """Search the company handbook and documents for information.

    Args:
        query: What to look for, e.g. 'annual leave days' or 'intern allowance'.

    Returns:
        The most relevant passages from the documents.
    """
    hits = retrieve(query, k=2)  # less text = faster on a laptop CPU
    return "\n---\n".join(f"[{label(m)}] {doc}" for doc, m in hits)


def get_current_date() -> str:
    """Get today's date and time.

    Returns:
        The current date and time.
    """
    return datetime.datetime.now().strftime("%A %d %B %Y, %H:%M")


def save_note(text: str) -> str:
    """Save a note to the notes.md file for the user.

    Args:
        text: The content of the note to save.

    Returns:
        Confirmation message.
    """
    with open("notes.md", "a", encoding="utf-8") as f:
        f.write(f"- {datetime.datetime.now():%Y-%m-%d %H:%M} — {text}\n")
    return "Note saved to notes.md"


TOOLS = {f.__name__: f for f in [calculator, search_documents, get_current_date, save_note]}

SYSTEM_PROMPT = """You are a helpful assistant with tools. Call ONE tool at a time and wait for its result.
Follow this order:
1. search_documents to find the facts (company rules, numbers).
2. calculator for ANY arithmetic, even simple. Never do math in your head.
3. save_note ONLY if the user asked to save something, and ONLY after you have the final result.
   The note must contain the final result.
4. Then give a short final answer (one or two sentences)."""


# ---------- The agent loop ----------
def run_agent(task: str, max_steps: int = 6, verbose: bool = True) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]
    for step in range(1, max_steps + 1):
        t0 = time.time()
        response = client.chat(model=AGENT_MODEL, messages=messages, tools=list(TOOLS.values()),
                               keep_alive=KEEP_ALIVE, options=OPTIONS)
        msg = response.message
        messages.append(msg)

        if not msg.tool_calls:          # no tool needed → final answer
            return msg.content
        if verbose:
            print(f"[step {step}] the model chose a tool ({time.time() - t0:.1f}s)")

        for call in msg.tool_calls:
            name, args = call.function.name, call.function.arguments
            fn = TOOLS.get(name)
            try:
                result = fn(**args) if fn else f"Unknown tool: {name}"
            except Exception as e:
                result = f"Tool error: {e}"
            if verbose:
                print(f"   tool  {name}({args}) → {str(result)[:90].replace(chr(10), ' ')}…")
            messages.append({"role": "tool", "content": str(result), "tool_name": name})

    return "I stopped because the task needed too many steps."


if __name__ == "__main__":
    task = " ".join(sys.argv[1:]) or (
        "I'm a full-time employee. I took 7 days of leave in March and 5 in August. "
        "How many leave days do I have left? Save the answer as a note."
    )
    print(f"Task: {task}\n")
    print(f"\nAnswer: {run_agent(task)}")
