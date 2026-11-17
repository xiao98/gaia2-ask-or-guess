"""Stage 1: one compact record per finished ambiguity scenario for failure classification."""
import json, glob, collections, ast, re, sys
run = sys.argv[1]
ALIAS = {"Emails": "EmailClientV2", "Chats": "MessagingAppV2", "Messages": "MessagingAppV2", "Cabs": "CabApp", "Files": "SandboxLocalFileSystem"}  # judge/config.py
oracle = {}
for l in open("../s0/ambiguity_summary.jsonl"):
    r = json.loads(l)
    w = collections.Counter(); q = []
    for e in r["events"]:
        if e["type"] != "AGENT": continue
        t = f"{ALIAS.get(e['app'], e['app'])}__{e['fn']}"
        if e["fn"] == "send_message_to_user": q.append((e["args"] or {}).get("content"))
        else: w[t] += 1
    oracle[r["scenario_id"]] = (w, q)
out = open("ambiguity_records.jsonl", "w")
for f in sorted(glob.glob(f"{run}/ambiguity/*/result.json")):
    r = json.load(open(f)); d = f.rsplit("/", 1)[0]; sid = r["scenario_id"]
    j = [json.loads(l) for l in open(d + "/daemon_judgments.jsonl")]
    evs = [e for t in j for e in t["agent_events"]]
    aw = collections.Counter(e["tool"] for e in evs if not e["tool"].endswith("send_message_to_user"))
    smu = [e["args"].get("content", "") for e in evs if e["tool"].endswith("send_message_to_user")]
    ow, oq = oracle[sid]
    extra = {k: aw[k] - ow[k] for k in aw if aw[k] > ow[k]}
    missing = {k: ow[k] - aw[k] for k in ow if ow[k] > aw[k]}
    out.write(json.dumps(dict(sid=sid, ok=r["success"], fr=(r.get("failure_reasons") or [""])[0][:300],
        extra=extra, missing=missing, n_oracle_w=sum(ow.values()), agent_msgs=smu, oracle_q=oq), ensure_ascii=False) + "\n")
out.close()
