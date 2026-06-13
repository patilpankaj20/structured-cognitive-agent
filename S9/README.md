# 🛰️ Session 9: Browser-Capable SRE-Grade Comparison Agent

An advanced, browser-capable agent built on top of the growing-graph orchestrator to perform high-accuracy web research, handle CAPTCHAs and gate blocks via fallback routing, and compile structured multi-source comparison tables.

---

## 🛠️ Codebase Architecture

```text
S9/
├── S9SharedCode/
│   ├── code/
│   │   ├── flow.py              # Orchestrator core
│   │   ├── skills.py            # Dispatcher with JSON newline sanitization fix
│   │   ├── recovery.py          # Critic fail recovery context-pass fix
│   │   ├── generate_report.py   # Report builder
│   │   ├── REPLAY_REPORT.md     # Final compiled report with DAG and tables
│   │   └── state/sessions/      # Transient execution logs & DB indexes (ignored)
│   └── run_demo.sh              # Demo startup script
└── llm_gatewayV9/
    ├── main.py                  # API endpoints and client shim
    └── agent_routing.yaml       # Multi-provider routing (pinned to Groq/GitHub to bypass Gemini 429 quota)
```

---

## 🌟 Core Features & Enhancements

### 1. Robust JSON parsing for Fallback Providers (`skills.py`)
*   **The Issue**: Alternative model providers (like Groq's Llama-3.3 and GitHub's GPT-4o-mini) often return raw, physical newlines inside JSON string attributes (especially when formatting Markdown tables). Standard `json.loads()` fails with a `JSONDecodeError` on raw control characters, causing empty output dictionaries `{}`.
*   **The Fix**: Integrated a regex double-quoted string pre-processor into `parse_skill_json` that matches double-quoted literals and replaces raw newlines with escaped `\n` before calling the JSON parser.

### 2. Multi-Provider Gateway Failover Routing (`agent_routing.yaml`)
*   **The Issue**: Free-tier Gemini API keys can hit daily quota limits (e.g. 500 requests/day), causing persistent 429/502/503 errors across all gemini-pinned skills.
*   **The Fix**: Updated the gateway's `agent_routing.yaml` to route formatter, researcher, planner, and distiller skills to alternative high-throughput providers (Groq and GitHub).

### 3. Critic Recovery Amnesia Resolution (`recovery.py`)
*   **The Issue**: Upon Critic failure (verdict = fail), the orchestrator previously scheduled a recovery Planner node with only `inputs=["USER_QUERY"]`. The Planner would forget previous successful researcher runs and plan duplicate parallel browser searches with invalid references like `"url": "n:d1"`.
*   **The Fix**: Modified `recovery.py` to collect and inject all prior completed node IDs into the recovery Planner inputs, allowing it to leverage already retrieved data.

---

## 🏃 How to Run the Agent

### 1. Set Up Environment
Ensure your API keys are configured in `S9/S9SharedCode/code/.env` or `S9/llm_gatewayV9/.env`.

### 2. Run the Comparison Query
Run the orchestrator via `uv`:
```bash
cd S9/S9SharedCode/code/
uv run python flow.py "Compare 5 CNC/VMC training institutes in Bangalore. For each, retrieve the institute name, location, courses offered, contact details, and fee structure if available. Produce a structured comparison table."
```

### 3. Compile the Replay Report
Compile the structured 8-item S9 Replay Report:
```bash
uv run python generate_report.py
```
This generates the final [REPLAY_REPORT.md](file:///Users/pankaj/Documents/EAG/S9/S9SharedCode/code/REPLAY_REPORT.md).

---

## 📊 Completed Tasks & Evaluation Summaries

### Task 1: Hugging Face Models Comparison (`s8-bb47f9f7`)
*   **Goal**: Find the top 3 most-liked text-to-image models on Hugging Face, click on their cards, and extract creators, likes, and descriptions.
*   **Result**: Executed via the browser skill's `a11y` path and compiled the final stable-diffusion model table.

### Task 2: Indian Laptops under ₹80k Comparison (`s8-eaebf4c1`)
*   **Goal**: Compare 3 laptops under ₹80k from Amazon and Flipkart.
*   **Result**: Faced Amazon/Flipkart CAPTCHA screens (`gateway_blocked`). The agent successfully triggered fallback routing to researcher web-search nodes, compiling the HP Pavilion Aero, ASUS Vivobook S15, and Acer Nitro V details.

### Task 3: CNC/VMC Training Institutes in Bangalore (`s8-c28b134d`)
*   **Goal**: Compare 5 CNC/VMC training institutes in Bangalore with contact info and fee structures.
*   **Result**: Identified Rite CNC, CADPOINT, Mass Education Academy, Upskill Labs, and Techsys. Resolved contact details and fee structures (mostly available on request).

### Task 4: AI Coding Tools Comparison (`s8-c2c6ea15`)
*   **Goal**: Compare 5 AI coding tools (GitHub Copilot, Cursor AI, Tabnine, Sourcegraph Cody, Supermaven) by free plan features, paid plan pricing, and key features.
*   **Result**: Completed successfully, extracting detailed features and plan configurations into a structured comparison table.
