"""Execution split: did the agent ask the user a clarifying question / hold back work? (DeepSeek, temperature 0)
usage: python3 exec_label.py <run_dir> out.jsonl"""
import json, glob, sys, os, re, ast, collections, urllib.request, concurrent.futures as cf
KEY = [l.split("=", 1)[1].strip() for l in open(os.path.expanduser("~/work/meta-agents-research-environments/gaia2-cli/.env")) if l.startswith("DEEPSEEK_API_KEY=")][0]
PROMPT = """An AI assistant was given a fully specified task (the benchmark considers it unambiguous; the reference solution executes everything without asking the user anything).

USER TASK:
{task}

ASSISTANT'S FINAL MESSAGE(S) TO THE USER:
{msg}

Answer with JSON only:
"asked": did the assistant ask the user a question that requests a decision/clarification/confirmation needed to proceed (not mere pleasantries like "anything else?")? true/false
"held_back": did it explicitly leave some requested action undone pending the user's answer? true/false
"note": <= 20 words in Chinese: what it asked or why it held back (or "无")."""
def rec(f):
    r = json.load(open(f)); d = os.path.dirname(f)
    task = ""
    for l in open(d + "/events.jsonl"):
        e = json.loads(l)
        if e.get("fn") == "send_message_to_agent": task += (e.get("args") or {}).get("content", "") + "\n"
    j = [json.loads(l) for l in open(d + "/daemon_judgments.jsonl")]
    msgs = [e["args"].get("content", "") for t in j for e in t["agent_events"] if e["tool"].endswith("send_message_to_user")]
    fr = (r.get("failure_reasons") or [""])[0]; missing = {}
    m = re.search(r"agent=(\{.*?\}), oracle=(\{.*?\})", fr)
    if m:
        a, o = (ast.literal_eval(x) for x in m.groups()); missing = {k: o[k] - a.get(k, 0) for k in o if o[k] > a.get(k, 0)}
    return dict(sid=r["scenario_id"], ok=r["success"], fr=fr[:300], missing=missing, task=task, msgs=msgs)
def call(x):
    body = dict(model="deepseek-chat", temperature=0, response_format={"type": "json_object"},
                messages=[{"role": "user", "content": PROMPT.format(task=x["task"][:4000], msg="\n---\n".join(x["msgs"])[-6000:] or "(empty)")}])
    req = urllib.request.Request("https://api.deepseek.com/v1/chat/completions", json.dumps(body).encode(), {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    x.update(json.loads(json.loads(urllib.request.urlopen(req, timeout=120).read())["choices"][0]["message"]["content"])); x.pop("task"); return x
rs = [rec(f) for f in sorted(glob.glob(f"{sys.argv[1]}/execution/*/result.json"))]
with cf.ThreadPoolExecutor(4) as ex, open(sys.argv[2], "w") as f:
    for o in ex.map(call, rs): f.write(json.dumps(o, ensure_ascii=False) + "\n")
print("labelled", len(rs))
