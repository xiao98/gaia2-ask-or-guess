"""Paired comparison baseline vs intervention on the same subset.
usage: python3 compare.py <dir with baseline labels (s1)> <dir with intervention labels>"""
import json, sys, math
sub = json.load(open("subset_60a_40e_seed0.json"))["splits"]
def load(d):
    R = {json.loads(l)["sid"]: json.loads(l) for l in open(f"{d}/ambiguity_records.jsonl")}
    L = {json.loads(l)["sid"]: json.loads(l) for l in open(f"{d}/labels.jsonl")}
    E = {json.loads(l)["sid"]: json.loads(l) for l in open(f"{d}/exec_labels.jsonl")}
    amb = {}
    for s in sub["ambiguity"]:
        r = R[s]; l = L.get(s, {})
        amb[s] = dict(passed=r["ok"], missed=(not r["ok"]) and bool(l.get("acted_on_it")),
                      asked_held=r["ok"] or (bool(l.get("asked_same_point")) and not l.get("acted_on_it")))
    ex = {s: dict(passed=E[s]["ok"], overask=bool(E[s]["asked"])) for s in sub["execution"]}
    return amb, ex
def mcnemar(a, b, key, ids):
    n01 = sum(1 for s in ids if not a[s][key] and b[s][key]); n10 = sum(1 for s in ids if a[s][key] and not b[s][key])
    n = n01 + n10
    p = min(1.0, 2 * sum(math.comb(n, k) for k in range(0, min(n01, n10) + 1)) / 2 ** n) if n else 1.0
    return n10, n01, p
(ba, be), (ia, ie) = load(sys.argv[1]), load(sys.argv[2])
A, X = sub["ambiguity"], sub["execution"]
rows = [("歧义·该问没问(在歧义点动手)", ba, ia, "missed", A), ("歧义·问了且没乱动", ba, ia, "asked_held", A), ("歧义·整题通过", ba, ia, "passed", A),
        ("执行·不该问却问了", be, ie, "overask", X), ("执行·整题通过", be, ie, "passed", X)]
print(f"{'指标':<22}{'基线':>8}{'干预':>8}   基线是/干预否  基线否/干预是  McNemar p")
for name, b, i, k, ids in rows:
    nb = sum(b[s][k] for s in ids); ni = sum(i[s][k] for s in ids); n10, n01, p = mcnemar(b, i, k, ids)
    print(f"{name:<22}{nb:>4}/{len(ids):<3}{ni:>4}/{len(ids):<3}   {n10:>8}      {n01:>8}      {p:.3f}")
