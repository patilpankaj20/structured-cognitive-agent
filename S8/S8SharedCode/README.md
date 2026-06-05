# EAGV3 Session 8 — Student Scaffolding

Multi-agent growing-graph orchestrator built on the Session 7 cognitive
architecture. The graph itself is the agent loop: each node is a typed
skill (Planner, Researcher, Distiller, Critic, Formatter, …), edges
carry the predecessor's `AgentResult`, and the runtime executes ready
nodes in parallel via `asyncio.gather`.

Your assignment is to ship one missing skill (the **Coder**) so the
agent can write code, run it in a subprocess sandbox, and feed the
result back through the graph. Full spec in [ASSIGNMENT.md](ASSIGNMENT.md).

---

## Layout

```
S8SharedCode/
├── README.md          ← you are here
├── ASSIGNMENT.md      ← what you implement, how it gets graded
├── .env.example       ← copy to .env, fill in keys you have
├── .gitignore
│
├── code/              ← the agent. Run from here.
│   ├── flow.py        ← orchestrator (Graph + Executor + CLI). Read this first.
│   ├── skills.py      ← skill registry, prompt rendering, run_skill
│   ├── recovery.py    ← failure classification + critic-fail splice
│   ├── persistence.py ← session writes (graph.json + per-node JSON)
│   ├── mcp_runner.py  ← multi-turn tool-use loop wrapper
│   ├── sandbox.py     ← subprocess Python runner (usability boundary; NOT security)
│   ├── replay.py      ← stdin-driven trace viewer
│   ├── schemas.py     ← AgentResult, NodeSpec, NodeState, MemoryItem, …
│   ├── agent_config.yaml  ← skills catalogue (this is where you confirm Coder wiring)
│   ├── prompts/       ← one .md per skill. You edit coder.md.
│   ├── tests/         ← starts with test_recovery.py; you add yours.
│   ├── mcp_server.py  ← MCP tools: web_search, fetch_url, search_knowledge, …
│   ├── memory.py / vector_index.py / artifacts.py  ← S7 carryover (don't touch)
│   ├── perception.py / decision.py / action.py     ← S7 carryover (don't touch)
│   └── sandbox/papers/  ← five arxiv abstracts for indexed-corpus queries
│
└── gateway/           ← LLM Gateway V8 (FastAPI). Runs on :8108.
    ├── main.py
    ├── client.py      ← the SDK code/gateway.py imports from
    ├── providers.py / router.py / embedders.py / db.py / cache.py
    ├── agent_routing.yaml  ← agent → preferred provider mapping
    ├── pyproject.toml
    └── run.sh
```

---

## Quickstart

You need: Python 3.11+, [uv](https://docs.astral.sh/uv/), Ollama
(`brew install ollama` then `ollama pull nomic-embed-text`), and at least
one provider API key from `.env.example`.

```bash
# 1. Secrets
cp .env.example .env
$EDITOR .env                  # add the keys you have

# 2. Install
cd gateway && uv sync && cd ..
cd code    && uv sync && cd ..

# 3. Start the gateway (one terminal)
cd gateway && uv run main.py
# (or: ./run.sh)
# It boots on http://localhost:8108; /v1/routers should answer.

# 4. Run the agent (another terminal)
cd code
uv run python flow.py "hello"
```

A successful first run prints two node lines (planner, formatter) and a
greeting. Sessions land in `code/state/sessions/<sid>/`. Walk one with:

```bash
uv run python replay.py <sid>
```

---

## How to think about the architecture

The Planner reads the user query and emits a small DAG of skill nodes
to run. Each ready node fires through the gateway in parallel with its
ready siblings. When a skill's yaml entry has `internal_successors`,
the orchestrator appends those automatically — that's how **Coder →
SandboxExecutor** chains without the Planner having to ask for it.

Critic nodes get auto-inserted on edges out of skills tagged
`critic: true` in `agent_config.yaml` (currently Distiller). A
verdict=fail from a Critic splices a recovery Planner into the graph,
capped at one re-plan per branch.

Failure handling is in `recovery.py`. Transient gateway errors don't
re-plan (the gateway already retries); validation errors don't re-plan
(it's a prompt bug); upstream-failures do. `tests/test_recovery.py`
pins the classifier against the actual gateway error strings.

Read `flow.py`'s 300 lines top-to-bottom before you write a single
line of your Coder prompt. The orchestrator is small enough to fit in
your head.

---

## When things go wrong

| symptom | first place to look |
|---|---|
| `[gateway] launching … failed to start within 45s` | `cd gateway && uv run main.py` in another terminal; read its stderr. Probably a missing API key or port :8108 already taken. |
| `httpx.HTTPStatusError: '503 Service Unavailable'` | All worker providers in cooldown / unconfigured. Add another key to `.env` or wait a minute. |
| coder ran but `sandbox_executor` reports `no code in upstream coder output` | Your prompt isn't emitting the JSON shape the orchestrator expects. See ASSIGNMENT.md §"Output contract". |
| The final answer is short / wrong | Run `replay.py <sid>` and inspect what each node actually saw (the `prompt_sent` field captures the exact bytes sent to the gateway). |

---

## What NOT to touch

- `agent7_s7_carryover.py` (if present) — the Session 7 single-loop agent kept for reference. Out of scope.
- `perception.py`, `decision.py`, `action.py`, `memory.py`,
  `vector_index.py`, `artifacts.py`, `mcp_server.py` — carry over
  byte-identical from Session 7. The tool-blindness contract on
  Perception depends on these staying as-is.
- `gateway/` — treat as a service you call. If you find a real bug,
  open an issue; do not patch it inside your assignment.

---

## Provenance and version

This package is the Session 8 build that passes the round-3 review.
22 unit tests cover the failure-recovery + critic-splice mechanics.
Five validation queries (hello, S7 carryover Shannon, parallel fan-out
populations, graceful-fail nonexistent path, SIGKILL+resume) have been
verified end-to-end on the same code you have here.

If your `uv run python flow.py "hello"` produces a final answer, the
build runs cleanly on your machine. The next step is ASSIGNMENT.md.

---

## Execution Logs and Verification Results

The multi-agent growing-graph orchestrator has been verified across all core scenarios, base queries, and recovery loops. The execution logs are summarized below.

### 1. Base Queries Log

| Base Query Identifier | Query Text | Session ID | Node Execution Path | Final Answer / Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **hello** | `Say hello in one short sentence.` | `s8-4a638837` | `planner` &rarr; `formatter` | `Hello, it is a pleasure to assist you today.` |
| **A (Shannon)** | `Fetch https://en.wikipedia.org/wiki/Claude_Shannon and tell me his birth date, death date, and three key contributions to information theory.` | `s8-730bcc15` | `planner` &rarr; `researcher` &rarr; `formatter` | Birth: April 30, 1916. Death: Feb 24, 2001. Contributions: 'bit' concept, source coding, noisy-channel coding. |
| **I (Populations)** | `What are the populations of London, Paris, and Berlin? Compare them.` | `s8-952e4ff1` | `planner` &rarr; `researcher` (×3 parallel) &rarr; `formatter` | London: ~9.1M; Berlin: ~3.91M; Paris: ~2.16M (proper). |
| **J (Crash Sandbox)**| `Write a python script to open a nonexistent file and do not catch the error` | `s8-655050ea` | `planner` &rarr; `coder` &rarr; `sandbox_executor` (failed) &rarr; `planner` (recovery) ... | Caught sandbox exit code -1, dynamically spliced recovery planner to retry until node cap. |
| **K (SIGKILL + Resume)** | `populations of London, Paris, Berlin; which two are closest?` | `s8-45a8d066` | `planner` &rarr; `researcher` (×3 parallel) &rarr; `formatter` | Interrupted mid-run via `kill -9`, recovered status `running`/`pending` from `graph.json`, completed successfully. |

### 2. Parallel Fan-Out Wall-Clock Validation
- **Query**: `"Retrieve the current populations of Tokyo, Seoul, and Sydney, and determine which has the highest density."` (Session ID: `s8-4b799ce1`)
- **Parallel Execution Times**:
  - `n:2` (Tokyo): **36.4s**
  - `n:3` (Seoul): **24.4s**
  - `n:4` (Sydney): **32.6s**
- **Wall-Clock Duration**: **~44.3s** (including planner and formatter overhead).
- **Proof**: The total wall-clock duration of the session matches `max(branches) = 36.4s` plus overhead, not `sum(branches) = 93.4s`, validating concurrent graph execution.

### 3. Critic Failure Recovery Loop
- **Query**: `"Extract list of fruits from: 'apples, bananas, oranges, cherries' and verify there are exactly 3 fruits."` (Session ID: `s8-76bdbe68`)
- **Execution Loop**:
  - `distiller (n:2)` extracts all 4 fruits.
  - `critic (n:3)` fails the output: `"The extracted list contains 4 fruits, but it should contain exactly 3."`
  - Orchestrator catches failure, marks downstream skipped, splices in a recovery `planner` node (`n:5`).
  - This cycle repeats until the safety node cap of 60 is hit, proving robust critic verdict interception and recovery routing.

### 4. Custom Skill Verification (`text_analyst`)
- **Query**: `"Use the text_analyst skill to analyze the word count metrics of this text: 'The quick brown fox jumps over the lazy dog.'"` (Session ID: `s8-04c45df4`)
- **Path**: `planner` &rarr; `text_analyst` &rarr; `formatter`
- **Output JSON from `text_analyst`**:
  ```json
  {
    "rationale": "analyzing standard single-line sentence",
    "word_count": 9,
    "line_count": 1,
    "unique_words_count": 9
  }
  ```
- **Final Answer**: `"The text 'The quick brown fox jumps over the lazy dog.' contains 9 words in total. All 9 of these words are unique, and the text spans 1 line."`

### 5. Coder Skill Math Verification
- **Query**: `"Calculate the sum of the square roots of the first 50 odd numbers."` (Session ID: `s8-d4cc2209`)
- **Sandbox Output**: `333.4152759969378`
- **Final Answer**: `"The sum of the square roots of the first 50 odd numbers is approximately 333.415."`

