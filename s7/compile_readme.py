import re
from pathlib import Path

# Paths
S7_DIR = Path(__file__).parent
TRACES_DIR = S7_DIR / "sandbox" / "traces"
README_PATH = S7_DIR / "README.md"

BASE_QUERY_TITLES = {
    "A": "Query A: Claude Shannon Wikipedia Ingestion & Synthesis (3 Iters Bound)",
    "B": "Query B: Tokyo Activities Weather-Conditional Planning (4-5 Iters Bound)",
    "C1": "Query C1: Mom's Birthday Persistent Fact Storage (3-4 Iters Bound)",
    "C2": "Query C2: Mom's Birthday Zero-Tool 1-Turn Instant Retrieval (1 Iter)",
    "D": "Query D: Python Asyncio Best Practices Multi-Search & Synthesis (4 Iters Bound)",
    "E": "Query E: Voyager 1 Space Mission Wikipedia Fetch & Golden Record (3-4 Iters Bound)",
    "F": "Query F: SpaceX Mars Objectives Boca Chica Weather Conditional Routing (4-5 Iters Bound)",
    "G1": "Query G1: ISS CRS-32 Schedule Log Storage (3-4 Iters Bound)",
    "G2": "Query G2: ISS CRS-32 Schedule Zero-Tool 1-Turn Instant Retrieval (1 Iter)",
    "H": "Query H: Next-Gen Space Telescopes Planned in 2030s Comparison (5-6 Iters Bound)"
}

CUSTOM_QUERY_TITLES = {
    "1": "Query 1: ResNet Bypass Layers Shortcut Mapping (Semantic Recall)",
    "2": "Query 2: DPO Implicit Reward Equations Preference Alignment (Semantic Recall)",
    "3": "Query 3: ReAct HotpotQA Success Rate vs CoT & Act Baselines (Specific Fact)",
    "4": "Query 4: LoRA GPT-3 175B Adaption Trainable Parameters & Memory Savings (Specific Fact)",
    "5": "Query 5: Transformer Scaled Dot-Product Attention Formula & Factor (Specific Fact)"
}

def clean_trace(text: str) -> str:
    """Strip out unnecessary terminal escape sequences or huge repetitions if any."""
    return text.strip()

def compile_base_traces() -> str:
    blocks = []
    for key, title in sorted(BASE_QUERY_TITLES.items()):
        trace_file = TRACES_DIR / f"base_{key}.txt"
        if not trace_file.exists():
            print(f"Warning: {trace_file.name} not found!")
            continue
        
        content = clean_trace(trace_file.read_text(encoding="utf-8"))
        blocks.append(f"""
<details>
<summary><b>📖 {title}</b></summary>

```text
{content}
```

</details>
""")
    return "\n".join(blocks)

def compile_custom_traces() -> str:
    blocks = []
    for key, title in sorted(CUSTOM_QUERY_TITLES.items()):
        rag_file = TRACES_DIR / f"custom_rag_{key}.txt"
        norag_file = TRACES_DIR / f"custom_norag_{key}.txt"
        
        rag_content = clean_trace(rag_file.read_text(encoding="utf-8")) if rag_file.exists() else "Trace not found!"
        norag_content = clean_trace(norag_file.read_text(encoding="utf-8")) if norag_file.exists() else "Trace not found!"
        
        blocks.append(f"""
### 🎯 {title}

<table>
<tr>
<td width="50%">
<h3>🟢 RAG-Enabled (With Corpus Index)</h3>
<p>The vector memory successfully matches query concepts, fetching precise chunks. The agent returns fully grounded factual data instantly.</p>
</td>
<td width="50%">
<h3>🔴 No-RAG Baseline (Without Index)</h3>
<p>Without retrieval, the agent falls back to web search or displays ignorance/hallucination since the target knowledge does not exist in its weights.</p>
</td>
</tr>
<tr>
<td>

<details>
<summary><b>🔍 View Grounded RAG Trace</b></summary>

```text
{rag_content}
```

</details>

</td>
<td>

<details>
<summary><b>⚠️ View No-RAG Failure Trace</b></summary>

```text
{norag_content}
```

</details>

</td>
</tr>
</table>

---
""")
    return "\n".join(blocks)

def main():
    if not README_PATH.exists():
        print("README.md not found!")
        return
        
    print("Compiling traces...")
    base_markdown = compile_base_traces()
    custom_markdown = compile_custom_traces()
    
    content = README_PATH.read_text(encoding="utf-8")
    
    # Replace placeholders
    content = content.replace("[TRACES_A_H_PLACEHOLDER]", base_markdown)
    content = content.replace("[TRACES_CUSTOM_PLACEHOLDER]", custom_markdown)
    
    README_PATH.write_text(content, encoding="utf-8")
    print("Successfully compiled and populated README.md!")

if __name__ == "__main__":
    main()
