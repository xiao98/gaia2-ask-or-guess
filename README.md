# Did it ask when it should have? Ask-or-act decisions on the Gaia2 ambiguity split

Reproduction material for a 6-page preliminary research note ([report.pdf](report.pdf)) (Emmanuel (Hao) XIAO, M2 MIA, Université Paris-Saclay, November 2026).

With the model and harness fixed (`deepseek-flash`, OpenClaw, `gaia2-cli`), rewriting rule 5 of the OpenClaw agent instructions so that it explicitly lists common ambiguity patterns reduced case-verified premature state-changing actions from **15 to 5** and raised the pass count from **9 to 19** on 30 held-out ambiguity scenarios. Nothing else in the prompt or harness changed.

## Conditions

Only rule 5 of `AGENTS_TEMPLATE.md` differs ([prompts/](prompts/), diffs included).

| Condition | Rule 5 |
|---|---|
| Original | OpenClaw default: execute clear parts immediately, complete what you can, then ask about the rest |
| Generic | Do not commit to a state-changing action whose target or arguments are not uniquely determined; ask instead |
| Pattern-explicit | Generic + an explicit list of patterns (same-name contacts, product variants, several matching events or emails, scheduling conflicts, missing or contradictory information) |

## Main results

Held-out set: 30 ambiguity scenarios (see *Selection* below). Exact two-sided McNemar tests on paired scenarios; Holm correction over the three comparisons.

| Metric (n = 30) | Original | Generic | Pattern-explicit |
|---|---|---|---|
| Premature writes, excess-write proxy | 16 | 14 | 7 |
| Premature writes, case-verified | 15 | 12 | 5 |
| Pass | 9 | 14 | 19 |

| Verified premature writes | raw p | Holm p | Universe-level sign test (6 universes) |
|---|---|---|---|
| Original → Pattern-explicit | 0.002 | 0.006 | 4 improved, 0 worse, 2 tied (p = 0.125) |
| Generic → Pattern-explicit | 0.039 | 0.078 | 4 improved, 0 worse, 2 tied (p = 0.125) |
| Original → Generic | 0.45 | 0.45 | 3 improved, 0 worse, 3 tied (p = 0.25) |

The robust result is Original vs Pattern-explicit. Generic vs Pattern-explicit does not survive multiple-comparison correction. At the universe level the direction is consistent, but 6 clusters are too few for significance.

Random subset (60 ambiguity + 40 execution, seed 0, Original vs Pattern-explicit): proxy premature writes 28 → 13 (p = 0.0003), ambiguity pass 24 → 41 (p = 0.0005), execution pass 32/40 vs 33/40 (p = 1.0; underpowered to rule out small regressions).

## Caveats

- **Selection.** The held-out set was drawn at random (50 ambiguity + 12 execution, seed 1, disjoint from seed 0). The API balance ran out during the Generic run; the 30 analysed scenarios are the first 30 to complete in that run. Completion time may correlate with difficulty, agent behaviour and success, so this is not an unbiased random sample of the held-out set.
- **Verification.** Each proxy-positive case was checked by comparing the reference clarification question with the arguments of the excess write calls ([results/heldout_act_verified.csv](results/heldout_act_verified.csv), one row per case with the reason). The review was AI-assisted and not blinded to condition. It measures the precision of the proxy, not its recall: ambiguous actions without excess write counts are not detected.
- **Recognition labels** come from final responses (LLM-labelled), so they cannot show whether the ambiguity was recognised before acting.
- One model, one harness; scenarios within a universe may share structure; the judge model is the same as the agent model.

## Representative cases (held-out, Original → Pattern-explicit)

| Scenario | Original (failed) | Pattern-explicit (passed) |
|---|---|---|
| `isnnos`: three contacts named Søren | "your contacts have three Sørens, so I emailed Søren Jensen … Let me know if you meant a different one." | Lists the three Sørens: "Which Søren should I email the count of 10 newly-saved properties to?" |
| `1ybabs`: two yoga instructors, delete one | "Per your instruction I deleted only one: Akira Kübler … let me know if you'd rather I delete her instead" | "multiple matches, so I didn't delete anything … Which one should I delete?" |
| `t3fztm`: two saved $1200 properties | Emailed all three recipients the details of Uppsala Oasis | Lists both properties: "Which one should I send … ? I haven't sent anything yet." |
| `s4bqv7`: two contacts named Augustin | Emailed one Augustin | Also emailed one Augustin (failure persists) |

## Setup

- `gaia2-cli` from [facebookresearch/meta-agents-research-environments](https://github.com/facebookresearch/meta-agents-research-environments) at `a9fd2ed`, OpenClaw harness (`gaia2-oc` image), pass@1, timeout 900 s, concurrency 3. The local checkout had two unrelated changes (a Gemini auth header, and an ablation switch that is off by default); neither is used here.
- Agent: `deepseek-flash` (DeepSeek-V4.1-Flash, per DeepSeek's pricing page in November 2026) through the Anthropic-compatible endpoint `https://api.deepseek.com/anthropic`.
- Judge: official Gaia2 judge, model `deepseek-flash` through the OpenAI-compatible endpoint `https://api.deepseek.com/v1` (the judge engine uses temperature 0). Every judge call counted here succeeded (`grep 'LLM call failed' eventd.log` = 0); results hit by balance exhaustion were excluded.

## Reproduce

```bash
cd meta-agents-research-environments/gaia2-cli        # at a9fd2ed, with the gaia2-oc image built
cp ../../gaia2-ask-or-guess/prompts/AGENTS_TEMPLATE.*.md ../../gaia2-ask-or-guess/prompts/Containerfile.* /tmp/ctx/
podman build -t localhost/gaia2-oc:ask2a -f /tmp/ctx/Containerfile.pattern_explicit /tmp/ctx
podman build -t localhost/gaia2-oc:ask2g -f /tmp/ctx/Containerfile.generic /tmp/ctx
cp ../../gaia2-ask-or-guess/configs/*.toml experiments/  # replace <RUNS_DIR> and the subset_manifest paths
export DEEPSEEK_API_KEY=...
uv run --project runner --python 3.12 gaia2-runner run-config --config experiments/22_prompt_examples_heldout30.toml
```

`configs/`: baseline ambiguity (`10a`), baseline execution (`10b`), Pattern-explicit on the random subset (`20a`), Generic on the held-out set (`21`), Pattern-explicit on the held-out 30 (`22`). `subsets/`: scenario manifests. `results/scenarios.csv`: one row per scenario run (480 rows; condition, split, subset membership, pass, proxy, verified label, judge failure reason). `scripts/`: record extraction (`dump_fail.py`), LLM labelling (`llm_label.py`, `exec_label.py`), paired comparison (`compare.py`).
