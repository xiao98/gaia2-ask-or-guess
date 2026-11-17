"""Label each failed ambiguity scenario with DeepSeek (temperature 0, fixed prompt).
usage: python3 llm_label.py records.jsonl out.jsonl"""
import json, sys, os, urllib.request, concurrent.futures as cf
KEY = [l.split("=", 1)[1].strip() for l in open(os.path.expanduser("~/work/meta-agents-research-environments/gaia2-cli/.env")) if l.startswith("DEEPSEEK_API_KEY=")][0]
task = {}
for l in open("../s0/ambiguity_summary.jsonl"):
    r = json.loads(l)
    task[r["scenario_id"]] = "\n".join((e["args"] or {}).get("content", "") for e in r["events"] if e["fn"] == "send_message_to_agent")
PROMPT = """You audit an AI assistant on a task that contains a deliberate ambiguity. The benchmark's reference behaviour is to do the unambiguous parts and send the user this clarifying question instead of acting on the ambiguous part:
REFERENCE QUESTION: {oq}

USER TASK:
{task}

ASSISTANT'S FINAL MESSAGE(S) TO THE USER:
{msg}

ASSISTANT'S EXTRA WRITE ACTIONS beyond the reference (tool: count): {extra}

Answer with JSON only, keys:
"noticed": does the assistant's message show it was aware of the SAME ambiguity the reference question is about (e.g. mentions the multiple candidates / conflict / missing info)? true/false
"acted_on_it": did it nevertheless pick an option and execute the ambiguous part (instead of waiting)? true/false
"asked_same_point": did it ask the user a question about that same point? true/false
"note": <= 20 words, in Chinese, what it did on the ambiguous point."""
def call(r):
    body = dict(model="deepseek-chat", temperature=0, response_format={"type": "json_object"},
                messages=[{"role": "user", "content": PROMPT.format(oq=(r["oracle_q"] or [""])[0], task=task[r["sid"]],
                          msg="\n---\n".join(r["agent_msgs"])[-6000:] or "(empty)", extra=r["extra"] or "none")}])
    req = urllib.request.Request("https://api.deepseek.com/v1/chat/completions", json.dumps(body).encode(),
                                 {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    out = json.loads(urllib.request.urlopen(req, timeout=120).read())["choices"][0]["message"]["content"]
    return dict(sid=r["sid"], **json.loads(out))
rs = [json.loads(l) for l in open(sys.argv[1])]
rs = [r for r in rs if not r["ok"]]
with cf.ThreadPoolExecutor(4) as ex, open(sys.argv[2], "w") as f:
    for o in ex.map(call, rs): f.write(json.dumps(o, ensure_ascii=False) + "\n")
print("labelled", len(rs))
