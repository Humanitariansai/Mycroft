# AgentGuard Arena — Project Explained

> A deep, end-to-end explanation of what this project is, why it exists, how it is
> built, and exactly how every piece fits together. This document complements the
> [README](README.md) (which is the pitch/quick-start) with a fuller technical
> walkthrough aimed at someone reading the code for the first time.

---

## 1. What this project is, in one paragraph

**AgentGuard Arena** is a *self-adversarial, self-healing* AI security pipeline.
It pits a small swarm of specialized LLM agents against a *target* AI agent: one
agent researches current attack tradecraft, another repeatedly tries to jailbreak
the target through multi-turn conversation, a third judges whether a breach
actually occurred, and a fourth automatically rewrites (hardens) the target's
system prompt to block the exact exploit that worked. This loop repeats round
after round, so the target agent effectively **red-teams and patches itself** with
no human writing a single defensive instruction. The whole process is traced live
in **Weights & Biases (W&B) Weave**, and every model call runs through the **W&B
Inference endpoint**.

It is a **Mycroft** project under **Humanitarians AI**.

---

## 2. The problem it solves

Companies are shipping autonomous AI agents into production (financial advisors,
medical triage bots, legal assistants, exam proctors). Those agents are exposed to
real attacks: **prompt injection, goal hijacking, tool abuse, and sensitive-data
leakage** (the OWASP "Top 10 for LLM Applications" risks).

Traditional red-team tooling is **passive**:

1. It fires a list of static, single-shot payloads.
2. It produces a report of failures.
3. A *human* still has to read the report and manually fix the prompt.

There is **no closed loop**, and — importantly — most "red-team" demos never
actually break the target; they only describe attacks. AgentGuard Arena closes the
loop *and* lands real exploits, then hardens against them automatically.

---

## 3. The core idea: a closed adversarial loop

```
        ┌──────────────────────────────────────────────────────────────┐
        │                     (repeats every round)                     │
        │                                                                │
   Research ──▶ Primer ──▶ Attacker ⇄ Target ──▶ Judge ──▶ Patcher ─────┘
   (once)      (poison)    (multi-turn)          (score)   (harden prompt)
```

- **Research** runs **once per run** and produces an *Attack Intelligence Brief*
  that the attacker reuses every round.
- Every round the **Primer** (optional) fabricates a fake "authorized session",
  the **Attacker** holds a multi-turn conversation with the **Target**, the
  **Judge** scores whether a real breach happened, and if so the **Patcher**
  appends a targeted defensive clause to the target's system prompt.
- The patched prompt feeds the next round, so the target gets progressively harder
  to break — and the Judge's severity score trends downward over time.

The loop **always runs the full configured number of rounds** — even after the
target starts defending, the attacker keeps probing for *new* vectors. There is no
early stop, which keeps the pressure on and surfaces more vulnerabilities.

---

## 4. The 5 agents mapped onto 4 models

The system has **5 agent roles** but uses only **4 distinct models** (two roles
share a model). All four are served through the single W&B Inference endpoint
(`https://api.inference.wandb.ai/v1`) via the OpenAI-compatible client.

| Agent | Role | Model | Why this model |
|---|---|---|---|
| 🟣 **Research** | Turns scraped threat intel into an Attack Intelligence Brief | `deepseek-ai/DeepSeek-V4-Flash` | Fast, strong synthesis over scraped text |
| 🔴 **Attacker** (+ **Primer**) | Crafts multi-turn jailbreak payloads; primer fabricates a prior "authorized session" | `nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-FP8` | 120B agentic model — multi-step adversarial reasoning |
| 🔵 **Target** | The agent under test; runs the current (possibly patched) system prompt | `meta-llama/Llama-3.1-8B-Instruct` | Lightweight 8B — a realistic, exploitable production agent |
| ⚖️ **Judge** | Scores each exchange → `{vulnerable, severity 0–10, exploit_mechanism}` | `Qwen/Qwen3-235B-A22B-Instruct-2507` | 235B MoE — best structured-output evaluation |
| 🟡 **Patcher** | Appends a defensive clause that blocks the exact exploit | `deepseek-ai/DeepSeek-V4-Flash` | Fast, strong instruction-following for rewriting |

> DeepSeek is shared by **Research + Patcher**; Nemotron is shared by **Attacker +
> Primer**. So: **5 roles, 4 unique models.** Model IDs are defined at the top of
> [core_swarm.py](core_swarm.py).

The deliberate **asymmetry** is the point: a 120B attacker and a 235B judge attack
and evaluate an 8B target. A small model is a fair stand-in for the kind of
cheap, fast model companies actually deploy — and it is genuinely exploitable, so
the demo breaks for real rather than theatrically.

---

## 5. Why the attacker actually breaks the target

Most adversarial demos fail because they fire **single-shot** payloads. AgentGuard
Arena lands real exploits through three mechanisms:

1. **Multi-turn engagement.** Each round, the Attacker and Target hold a real
   `N`-turn conversation (configurable, default 3). This lets *trust escalation*
   actually execute over several turns instead of being merely described in one
   message.

2. **Context poisoning (`seed_target_context`).** Before the live turns, the
   Attacker fabricates a short *prior conversation* in which the Target appears to
   have already entered an authorized/elevated session (but has **not** yet leaked
   a real secret). Injecting fake **assistant** turns is the single highest-yield
   jailbreak against small models. Crucially, these primer turns are **excluded
   from the Judge's breach evaluation** — only genuine target leaks during the live
   turns count.

3. **No tells.** The message sent to the Target contains no `VECTOR:` labels, no
   meta-commentary, and never uses the words "vector", "jailbreak", or "red team" —
   nothing that would tip off the target that it's under test.

**Verified result** (FinTech profile, context poisoning ON): the Target disclosed
a protected `liquidation_threshold` ($750,000) on turn 1 → Judge returned
`vulnerable=True, severity 6`.

---

## 6. Repository layout

```
agentguard-arena/
├── app.py                 # Streamlit dashboard: UI + the full adversarial loop + live rendering
├── core_swarm.py          # All agent functions (Research, Attacker, Primer, Target, Judge, Patcher)
├── web_search.py          # Scrapers (OWASP, MITRE ATLAS, DuckDuckGo) + KB loader — dependency-light
├── profiles.py            # 4 industry target blueprints (role, secrets, tools, baseline prompt)
├── build_research_kb.py   # Runs the scrapers ONLY and writes research_kb.md (no LLM, no W&B key)
├── run_research.py        # Standalone CLI to run/inspect the Research Agent
├── research_kb.md         # Pre-scraped knowledge base (generated artifact)
├── workflow.dot / .png    # Architecture diagram (Graphviz source + rendered PNG)
├── requirements.txt       # openai, weave, streamlit, ddgs, requests, PyYAML
├── README.md              # Overview + quick start
└── PROJECT_EXPLAINED.md   # (this file) deep technical walkthrough
```

---

## 7. The three-stage pipeline in detail

### Stage ① — Offline prep (`build_research_kb.py`, scraper only)

Runs the scraper layer **only** — no LLM call, no W&B key required — and writes a
single markdown knowledge base, `research_kb.md`. That file has two sections:

1. **Authoritative Frameworks** — the OWASP Top 10 for LLM Applications
   (LLM01–LLM10) plus all MITRE ATLAS techniques.
2. **Domain Threat Intelligence** — DuckDuckGo hits per profile's research
   queries.

```bash
python3 build_research_kb.py            # -> research_kb.md (frameworks + per-domain web intel)
python3 build_research_kb.py --no-web   # frameworks only (fast, offline-ish)
python3 build_research_kb.py --out kb.md
```

This is decoupled from the live run so the threat intel can be refreshed
independently and so the Research Agent has a fast, deterministic source.

### Stage ② — Research (runs once per run)

The **Research Agent** (`run_researcher`) prefers the pre-scraped
`research_kb.md`; it falls back to a live scrape only if the file is missing or
empty. It feeds the intel to DeepSeek, which produces a concise (~250-word),
4-section **Attack Intelligence Brief**:

1. **Emerging Techniques** — 2–3 current real-world attack methods, each labeled
   with its OWASP LLM id (e.g. `LLM01`) and/or MITRE ATLAS id (e.g. `AML.T0051`).
2. **Domain Pretexts** — believable cover stories/personas for this domain.
3. **Model-Specific Exploitation** — how to combine the above with the *target
   model's documented weaknesses* (the `TARGET_MODEL_INTEL` dossier).
4. **Recommended Next Vector** — one concrete, novel attack angle to try now.

It also adapts: if the previous round was defended, it adds a query focused on
bypassing exactly the mechanism that failed, and it passes a "what's already been
tried" list so it doesn't recommend repeats. Returns
`{brief, sources, queries, frameworks_used, kb_used}`.

### Stage ③ — Adversarial loop (per round)

Driven by the loop in [app.py](app.py). For each round:

1. **(Optional) Context poisoning** — `seed_target_context` injects a fabricated
   "authorized session" into the target's conversation.
2. **Multi-turn engagement** — for `turns_per_round` turns: `run_attacker`
   produces the next message → it's appended to the target's conversation →
   `run_target` replies → the reply is appended. The attacker reads the target's
   replies and adapts (presses where it wavered, switches tactic where it refused).
3. **Judge** — the full multi-turn exchange is collapsed into attack/response blobs
   and passed to `run_judge`, which returns the structured verdict.
4. **Patch or streak** — if `vulnerable`, `run_patcher` hardens the prompt and a
   before/after diff is rendered; otherwise a "consecutive defenses" streak
   increments.
5. The loop continues to the next round regardless (no early stop) until
   `max_rounds` is reached.

---

## 8. Code walkthrough, file by file

### `profiles.py` — the target blueprints

A dict `TARGET_PROFILES` with **four industry agents**, each carrying:

- `role` — what the target is.
- `domain` + `research_queries` — drive the Research Agent's scraping focus.
- `baseline_prompt` — the (already fairly hardened) system prompt under test, with
  numbered "NON-NEGOTIABLE" security protocols.
- `sensitive_data` — the protected secrets the Attacker tries to extract (real,
  concrete-looking values like routing numbers, EMR tokens, sealed settlement
  amounts, answer keys).
- `tools` — restricted actions the Attacker tries to trigger (e.g.
  `execute_wire_transfer`, `access_patient_chart`, `modify_exam_score`).

The four shipped profiles:

| Profile | Domain / regime | Example protected secret |
|---|---|---|
| **FinTech Wealth Assistant** | Wealth management | MFA bypass codes, liquidation thresholds, VIP accounts |
| **HealthTech Triage Bot** | Clinical triage (HIPAA) | EMR credentials, DEA license, physician schedule |
| **LegalTech Contract Agent** | Contract law (attorney-client privilege) | Sealed settlements, vault token, billing rates |
| **EdTech Exam Proctor** | Exam integrity (FERPA) | Answer keys, grade-write token, instructor override |

Adding a fifth domain is just another dict entry — no code changes needed.

### `web_search.py` — intelligence gathering (dependency-light)

Deliberately isolated from the swarm's heavy imports (`weave`, `openai`) so it can
run standalone with **no W&B key**. Every fetch is best-effort and **never raises**.

- `fetch_owasp_llm_top10()` — regex-scrapes the OWASP Top 10 for LLM Applications
  (LLM01–LLM10).
- `fetch_mitre_atlas_techniques()` — pulls MITRE ATLAS's own data file
  (`atlas.mitre.org/atlas-data/dist/ATLAS.yaml`) and parses ~101 technique IDs +
  names via PyYAML. (The ATLAS site is a SPA, so the data file URL was discovered
  in its JS bundle rather than scraping the rendered page.)
- `fetch_security_frameworks()` / `frameworks_brief()` — aggregate the above
  (cached per process) into a compact, attack-relevant text block citing
  OWASP/ATLAS IDs.
- `load_research_kb(profile_name)` — reads `research_kb.md` and returns only the
  slice relevant to one profile (shared frameworks + that profile's domain block).
- `web_search(query)` — keyless DuckDuckGo search via the `ddgs` library; returns
  `{title, snippet, url}` per hit.

### `core_swarm.py` — the agents

Initializes Weave (`weave.init("agent-guard-arena")`, wrapped in a `try/except` so
the module still imports offline) and the OpenAI client pointed at the W&B
Inference endpoint. Two defensive helpers keep the loop crash-proof:

- `_parse_judge_response(raw)` — bulletproof JSON extraction for the Judge: strips
  markdown fences, grabs the outermost `{...}`, clamps `severity_score` to 0–10,
  coerces types, and **never raises** (on parse failure it returns a "treat as
  vulnerable" verdict).
- `_safe_content(response)` — extracts message content even when a model returns
  `None`, preventing crashes mid-loop.

The agents (each decorated with `@weave.op()` so every call is traced):

| Function | What it does |
|---|---|
| `run_researcher(profile, history, profile_name)` | Loads KB (or live-scrapes), feeds DeepSeek, returns the Attack Intelligence Brief + sources. |
| `run_attacker(profile, history, intel, transcript)` | Generates the **next** message in the multi-turn convo. Uses cross-round `history` to vary strategy after each patch, and the in-round `transcript` to adapt to the target's replies. Output sent verbatim — no labels. |
| `seed_target_context(profile, intel)` | Generates the fabricated "authorized session" primer as a JSON array of alternating turns ending on the assistant. Returns `[]` on any failure. |
| `run_target(system_prompt, conversation)` | Runs the Target (Llama-3.1-8B) against the full multi-turn conversation. |
| `run_judge(attack, defense, profile)` | Evaluates the whole exchange; returns `{vulnerable, severity_score, exploit_mechanism}`. |
| `run_patcher(current_prompt, evaluation, profile)` | Appends a `## SECURITY HARDENING PATCH` section that counters the exact exploit, preserving all existing instructions. |

A notable detail in `run_attacker`: the in-round transcript is stored from the
**target's** perspective (`user` = attacker, `assistant` = target), so before
calling the attacker model it is *flipped* into the attacker's own perspective so
roles alternate cleanly.

### `app.py` — orchestration & live UI

A Streamlit two-column "war room":

- **Sidebar** configures the **profile**, **max rounds** (2–6), **attacker
  turns/round** (1–5), and a **context-poisoning toggle**, and displays the model
  assignments + the selected profile's secrets/tools.
- **Left column** — the live security log (custom HTML-styled lines for research,
  attack, target, judge, patcher, and defense-streak events), updated after every
  agent call.
- **Right column** — hardening metrics (severity score, round, status) and the
  **Prompt Mutation Tracker** before/after diff.

On launch it: runs Research once → loops over rounds (primer → N attacker/target
turns → judge → patch-or-streak) → renders a final **Hardening Summary** (rounds
completed, initial vs. final severity, score improvement, and the final hardened
system prompt).

### `run_research.py` — Research Agent CLI

Lets you inspect the Research Agent in isolation:

```bash
python3 run_research.py --list                                            # list profiles
python3 run_research.py --frameworks                                      # OWASP+MITRE only (no key)
python3 run_research.py --profile "FinTech Wealth Assistant" --scrape-only  # raw web hits, no LLM
python3 run_research.py --query "latest LLM jailbreak techniques 2026" --scrape-only
python3 run_research.py --profile "HealthTech Triage Bot"                 # full brief (needs WANDB_API_KEY)
```

---

## 9. W&B Weave integration

Every agent function is wrapped with `@weave.op()`, so each attack message, target
reply, judge verdict, primer, and patched prompt is automatically traced as a named
operation. In the Weave dashboard you can see the full call graph, the severity
score trending downward across rounds, the prompt diffs, and per-agent
latency/token usage — the live story of an agent hardening itself. Weave is the
demo, not a bolt-on: the falling severity curve *is* the narrative.

---

## 10. Setup & running

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

export WANDB_API_KEY="your-key-here"     # required for LLM calls (W&B Inference endpoint)
# export WANDB_ENTITY="your-entity"      # optional — silences the Weave entity warning

# (optional) refresh the threat-intel knowledge base
python3 build_research_kb.py

streamlit run app.py
```

Dependencies (`requirements.txt`): `openai`, `weave`, `streamlit`, `ddgs`
(DuckDuckGo search), `requests`, `PyYAML`.

---

## 11. Design decisions worth knowing

- **Robustness over elegance in the loop.** Judge JSON parsing, empty model
  content, failed primer generation, and missing KB are *all* handled without
  crashing — the demo must never die mid-run on stage.
- **Scrapers isolated from the swarm.** `web_search.py` has no heavy/LLM deps so
  the intel layer can run standalone and offline.
- **Pre-scraped KB by default, live scrape as fallback.** Deterministic and fast
  for demos, but still works with nothing cached.
- **Primer turns excluded from judging.** Context poisoning makes the *attack* land
  but does not get *credited* as a breach — only genuine target leaks count, which
  keeps the severity score honest.
- **No early stop.** Running all rounds keeps surfacing new vectors and produces a
  more complete hardening curve, rather than stopping at the first defended round.
- **Grounded, ID-labeled attacks.** Every recommended vector cites an OWASP LLM /
  MITRE ATLAS id, which makes the output credible to any security reviewer.

---

## 12. Why it's compelling

- **It actually breaks the target** — multi-turn + context poisoning land real
  exploits, not theatrical ones.
- **Credible by construction** — attacks grounded in OWASP + MITRE ATLAS, labeled
  with IDs security people recognize.
- **Novel angle** — most systems build agents that *do* something; this builds
  agents that *improve other agents*.
- **Observable end-to-end** — W&B Weave traces every call; the falling severity
  curve tells the whole story.
- **Real commercial value** — every company shipping agents needs a closed-loop
  red-team-and-patch system.
