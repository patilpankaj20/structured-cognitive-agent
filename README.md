# 🛰️ LEO Satellite Constellation Network Router & Operations Center

An advanced, high-fidelity multi-step agentic system driven by **Model Context Protocol (MCP)** that models terrestrial terminals in **London** and **New York**, handles orbital mechanics for a dense **54-satellite Low Earth Orbit (LEO) Constellation** (3 planes, 18 satellites per plane at 550 km altitude), performs 3D vector-sphere line-of-sight obstruction checking, solves Dijkstra network routing, and computes relative-velocity Doppler shift telemetry.

The project features a **Terminal Console Agent** with a structured Quality Auditor validation loop and an **Interactive 3D Web Dashboard** with real-time orbit playbacks and click-and-drag 3D camera controls.

---

## 🌟 Interactive 3D Operations Dashboard (FastAPI Web App)
We built a state-of-the-art browser interface serving live telemetry on **Port 8200**:
*   **3D HTML5 Canvas Orbit Viewer**: Click and drag to rotate the Earth sphere and watch all 54 LEO spacecraft orbit in 3D ECI coordinates.
*   **Dynamic Shortest-Path Overlay**: Visually overlays the active shortest-path route with thick, glowing neon lines and radar rings pulsing at ground stations.
*   **Simulation Time Control**: An interactive scrubber/slider ($t = 0$s to $1000$s) with an **Auto-Play** toggle, allowing you to watch the network graph and optimal path dynamically adapt as links break and form in real-time.
*   **Analytics Panels**: Elegant glassmorphic metrics cards showing latency gauges, path hop breakdowns, and Doppler tables with color-coded positive/negative frequency shifts.

---

## 🛠️ Codebase Architecture

```text
├── satellite_mcp.py        # FastMCP Server: Handles orbit math, line segment vector clamps, Dijkstra, and Doppler
├── satellite_agent.py      # CLI Agent: Native Session 5 executor loop, verifier, and 3D oblique Earth ASCII visualizer
├── satellite_web.py        # Web App: Serves the FastAPI server & the interactive 3D HTML5 operations dashboard
├── satellite_readme.md     # Student prompt qualification documentation and coordinate logs
└── README.md               # Main repository documentation & guide (This file)
```

---

## ⚙️ Mathematical & Physical Modeling

The constellation operates under rigorous physics calculations performed server-side by our MCP tools:

### 1. High-Fidelity Orbital Elements ($t$)
The 54 spacecraft are arranged in a $3 \times 18$ mesh with an inclination of $53.0^\circ$ and altitude of $550$ km ($R_{orbit} = 6921$ km). Mean motion (orbital angular velocity) is calculated using Earth's standard gravitational parameter:
$$\omega = \sqrt{\frac{GM_{Earth}}{R_{orbit}^3}}$$
Terrestrial stations are mapped into ECI coordinates under Earth rotation ($\Omega_{Earth} = 7.292115 \times 10^{-5}$ rad/s).

### 2. 3D Line-of-Sight Segment Clamping
To prevent communication signals from passing through the Earth bulk solid sphere, a 3D line-of-sight check is calculated. We find the closest point $P_{closest}$ along the transmitter-receiver segment to the Earth's center $(0,0,0)$ by projecting vectors:
$$u = -\frac{\vec{p}_1 \cdot \vec{v}}{\|\vec{v}\|^2}$$
If $0 < u < 1$, the closest point lies strictly inside the segment, and we ensure:
$$\|P_{closest}\| \ge R_{Earth} + 20\text{ km atmospheric buffer}$$

### 3. Dijkstra Shortest-Latency Routing
Graph meshes are built dynamically under strict connection range thresholds:
*   **Ground-to-Space**: $\le 2000$ km
*   **Space-to-Space**: $\le 2500$ km
Adjacency lists are constructed in a single call, and Dijkstra's algorithm solves the path of absolute minimum propagation latency (via speed of light $c \approx 299,792.458$ km/s).

### 4. Range Rate Doppler Shifts (10.0 GHz Links)
Instantaneous Doppler frequency shifts are computed by projecting the relative velocity vector of the spacecraft along the unit line-of-sight vector:
$$\Delta f = -f_0 \frac{\vec{v}_{relative} \cdot \vec{r}_{unit}}{c}$$
Where $f_0 = 10.0$ GHz ($1.0 \times 10^{10}$ Hz) and $\vec{v}_{relative} = \vec{v}_2 - \vec{v}_1$.

---

## 🚀 Qualified Prompt Engineering Standards

Our agent loop enforces strict prompt qualification standards designed for robust and reliable multi-turn tool workflows:

1.  **Explicit Reasoning**: The system prompt commands the model to strictly decouple math analysis from execution: *"never attempt to solve vector geometry, line-of-sight checks, or shortest path routing mentally."*
2.  **Structured Output Integration**: The auditor uses a strict Pydantic model (`RoutingVerdict`) via LLM Gateway V2 to confirm coordinates, link distances, path integrity, and formatting tolerances.
3.  **Separation of Reasoning & Tools**: The LLM agent functions as a high-level scheduler, while precise physics coordinates and Dijkstra meshes are calculated by the FastMCP tool registry.
4.  **Optimized Loop Throughput**: Rather than serial tool calls that exhaust LLM turn budgets, tools are refactored to take lightweight time parameters `t=100.0` and handle data loading server-side.

---

## 🏃 How to Run Locally

### 1. Launch the 3D Web Dashboard (Port 8200)
To experience the gorgeous click-and-drag 3D orbit viewer, auto-play simulation scrubber, and live pathing overlays:
```bash
uv run --with fastapi --with uvicorn --with mcp satellite_web.py
```
👉 Open your browser to: **[http://localhost:8200/](http://localhost:8200/)**

### 2. Run the Console Telemetry Agent Solver
To run the full executor solver loop, trigger the Pydantic Quality Auditor, and print the oblique 3D Earth wireframe console graphic:
```bash
uv run --with mcp --with pydantic satellite_agent.py
```

---

## 📊 Verified Console Telemetry Log Output

Below is the verified solver summary and oblique 3D wireframe console output generated at simulation time $t = 100.0$s:

```text
══════════════════════════════════════════════════════════════════════════════
🚀 Launching Multi-Step LEO Satellite Constellation Routing Agent V5
══════════════════════════════════════════════════════════════════════════════

📡 [Turn 1] Querying Constellation Operations Center...
   ↳ Provider : gemini (gemini-3.1-flash-lite-preview) | Latency: 1720 ms
   ↳ Dispatching 1 tool call(s) in parallel...
     ✅ get_node_positions({"t": 100}) ➜ {"London": {"pos": [3965.346, ...

📡 [Turn 2] Querying Constellation Operations Center...
   ↳ Provider : gemini (gemini-3.1-flash-lite-preview) | Latency: 1459 ms
   ↳ Dispatching 1 tool call(s) in parallel...
     ✅ find_shortest_path({"max_gs_range": 2000, "source": "London", "target": "New York", "max_ss_range": 2500, "t": 100}) ➜ {"path": ["London", "S42", "S41", "S40", "New York"], "total_latency_ms": 21.9139}

📡 [Turn 3] Querying Constellation Operations Center...
   ↳ Provider : gemini (gemini-3.1-flash-lite-preview) | Latency: 2023 ms
   ↳ Dispatching 1 tool call(s) in parallel...
     ✅ calculate_doppler_shift({"freq_hz": 10000000000, "vel1": [-0.001464, 0.289158, 0], "pos1": [3965.346, -20.0711, 4986.5088]...}) ➜ 81574.82

...

──────────────────────────────────────────────────────────────────────────────
📜 CONSTELLATION ROUTING OPERATIONS SUMMARY:
──────────────────────────────────────────────────────────────────────────────
The routing operation from London to New York at t = 100.0s has been completed. The optimal path utilizes three satellite hops.

### Routing Summary
*   **Path:** London → S42 → S41 → S40 → New York
*   **Total Propagation Latency:** 21.9139 ms
*   **Hop Count:** 4 hops (3 space-to-space, 2 ground-to-space)

### Doppler Shift Metrics (10.0 GHz Link)
| Hop | Link | Doppler Shift (Hz) |
| :--- | :--- | :--- |
| 1 | London → S42 | 81,574.82 |
| 2 | S42 → S41 | -0.01 |
| 3 | S41 → S40 | 0.00 |
| 4 | S40 → New York | -192,414.64 |
──────────────────────────────────────────────────────────────────────────────

🔍 Starting Structured Routing Verification...

📊 VERIFIED NETWORK ROUTING VERDICT:
   - Passed Verification: True
   - Reasoning          : The routing path is valid, and the latency and Doppler shift metrics are within expected operational tolerances for the specified time.
   - Source Station     : London
   - Destination Station: New York
   - Optimal Route Path : London ➜ S42 ➜ S41 ➜ S40 ➜ New York
   - Total Path Latency : 21.9139 ms
   - Wireless Link Hops : 4 hops
   - Max Doppler Shift  : 192414.64 Hz

══════════════════════════════════════════════════════════════════════════════
🛰️  LEO SATELLITE NETWORK ROUTING TELEMETRY GRAPH
══════════════════════════════════════════════════════════════════════════════
                                                                   
                                                                   
                    🛰️ 🛰️     🛰️  🛰️                +🛰️S41🛰️S42            
              🛰️🛰️                    🛰️   🛰️    +🛰️S40⚓Lon              
           🛰️                            🛰️   🗼New 🛰️                 
         🛰️🛰️                       🛰️        🛰️     🛰️      🛰️          
      🛰️                                     🛰️     🛰️                
            🛰️               🛰️                               🛰️      
       🛰️····· ·· · · · · · · · ·  · · ·🛰️· · · · · · ·· 🛰️····       
                 🛰️     🛰️                                     🛰️     
           🛰️      🛰️     🛰️        🛰️                       🛰️🛰️        
                  🛰️        🛰️                            🛰️          
                🛰️    🛰️     🛰️   🛰️                    🛰️🛰️             
                🛰️ 🛰️                 🛰️  🛰️     🛰️ 🛰️                   
                                                                   
                                                                   
══════════════════════════════════════════════════════════════════════════════
  Legend: ⚓ London (Source) | 🗼 New York (Dest) | 🛰️ Satellites | + Active Routing Hops
══════════════════════════════════════════════════════════════════════════════
```

---

---

## 🎥 Presentation Walkthrough
A complete video overview demonstrating the ECI physics equations, dynamic Dijkstra re-routing under time scrubbing, and the interactive web visualizer is available at:
*   **Submission Video Link**: [https://youtu.be/dummy-satellite-constellation-routing](https://youtu.be/dummy-satellite-constellation-routing) *(Placeholder for submission)*

---

## 📈 Session 8 Growing-Graph Multi-Agent Orchestrator Verification Logs

We have successfully completed all implementation and verification tasks for **Session 8: Multi-Agent Dynamic Growing-Graph Orchestrator**. Below are the verification logs for parts 1, 2, 3, 4, and 5 of the assignment.

To run the interactive demo runner displaying these runs:
```bash
cd S8/S8SharedCode/code/
uv run python demo.py
```

### 1. Base Verification Logs (Part 1, 4 & 5)

| Base Query Identifier | Query Text | Session ID | Node Execution Path | Final Answer / Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **hello** | `Say hello in one short sentence.` | `s8-4a638837` | `planner` &rarr; `formatter` | `Hello, it is a pleasure to assist you today.` |
| **A (Shannon)** | `Fetch https://en.wikipedia.org/wiki/Claude_Shannon and tell me his birth date, death date, and three key contributions to information theory.` | `s8-730bcc15` | `planner` &rarr; `researcher` &rarr; `formatter` | Birth: April 30, 1916. Death: Feb 24, 2001. Contributions: 'bit' concept, source coding, noisy-channel coding. |
| **I (Populations)** | `What are the populations of London, Paris, and Berlin? Compare them.` | `s8-952e4ff1` | `planner` &rarr; `researcher` (×3 parallel) &rarr; `formatter` | London: ~9.1M; Berlin: ~3.91M; Paris: ~2.16M (proper). |
| **J (Crash Sandbox)**| `Write a python script to open a nonexistent file and do not catch the error` | `s8-655050ea` | `planner` &rarr; `coder` &rarr; `sandbox_executor` (failed) &rarr; `planner` (recovery) ... | Caught sandbox exit code -1, dynamically spliced recovery planner to retry until node cap. |
| **K (SIGKILL + Resume)** | `populations of London, Paris, Berlin; which two are closest?` | `s8-45a8d066` | `planner` &rarr; `researcher` (×3 parallel) &rarr; `formatter` | Interrupted mid-run via `kill -9`, recovered status `running`/`pending` from `graph.json`, completed successfully. |

---

### 2. Parallel Fan-Out Wall-Clock Validation (Part 2)
* **Query**: `"Retrieve the current populations of Tokyo, Seoul, and Sydney, and determine which has the highest density."` (Session ID: `s8-4b799ce1`)
* **Parallel Execution Times**:
  - `n:2` (Tokyo): **36.4s**
  - `n:3` (Seoul): **24.4s**
  - `n:4` (Sydney): **32.6s**
* **Wall-Clock Duration**: **~44.3s** (including planner and formatter overhead).
* **Proof**: The total wall-clock duration of the session matches `max(branches) = 36.4s` plus overhead, not `sum(branches) = 93.4s`, validating concurrent graph execution.

---

### 3. Critic Failure Recovery Loop (Part 3)
* **Query**: `"Extract list of fruits from: 'apples, bananas, oranges, cherries' and verify there are exactly 3 fruits."` (Session ID: `s8-76bdbe68`)
* **Execution Loop**:
  - `distiller (n:2)` extracts all 4 fruits.
  - `critic (n:3)` fails the output: `"The extracted list contains 4 fruits, but it should contain exactly 3."`
  - Orchestrator catches failure, marks downstream skipped, splices in a recovery `planner` node (`n:5`).
  - This cycle repeats until the safety node cap of 60 is hit, proving robust critic verdict interception and recovery routing.

---

### 4. Custom Skill Verification (Part 4)
* **Query**: `"Use the text_analyst skill to analyze the word count metrics of this text: 'The quick brown fox jumps over the lazy dog.'"` (Session ID: `s8-04c45df4`)
* **Path**: `planner` &rarr; `text_analyst` &rarr; `formatter`
* **Output JSON from `text_analyst`**:
  ```json
  {
    "rationale": "analyzing standard single-line sentence",
    "word_count": 9,
    "line_count": 1,
    "unique_words_count": 9
  }
  ```
* **Final Answer**: `"The text 'The quick brown fox jumps over the lazy dog.' contains 9 words in total. All 9 of these words are unique, and the text spans 1 line."`

---

### 5. Coder Skill Sandbox Verification (Part 5)
* **Query**: `"Calculate the sum of the square roots of the first 50 odd numbers."` (Session ID: `s8-d4cc2209`)
* **Sandbox Output**: `333.4152759969378`
* **Final Answer**: `"The sum of the square roots of the first 50 odd numbers is approximately 333.415."`

