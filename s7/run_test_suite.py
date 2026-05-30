import asyncio
import io
import sys
from pathlib import Path

# Ensure s7 modules are importable
sys.path.insert(0, str(Path(__file__).parent))

import agent7
import memory as _memory

TRACES_DIR = Path(__file__).parent / "sandbox" / "traces"
TRACES_DIR.mkdir(parents=True, exist_ok=True)

BASE_QUERIES = {
    "A": "Fetch https://en.wikipedia.org/wiki/Claude_Shannon and tell me his birth date, death date, and three key contributions to information theory.",
    "B": "Retrieve 3 popular activities in Tokyo, find the Saturday weather forecast for Tokyo, and determine the most appropriate activity (indoor or outdoor) assuming rainy conditions.",
    "C1": "Remember that Mom's birthday is on 15 May 2026. Create a calendar reminder file named birthday_reminder.txt in the sandbox.",
    "C2": "When is Mom's birthday? Check your records and tell me.",
    "D": "Search for asyncio best practices, fetch the top 3 resulting URLs, synthesise their common advice, and output a clean numbered list of recommendations.",
    "E": "Fetch the Wikipedia page for Voyager 1 (https://en.wikipedia.org/wiki/Voyager_1) and tell me its launch date, its current estimated distance from Earth (in AU or km), and describe the three key components of the Golden Record carried on board.",
    "F": "Retrieve 3 primary mission objectives of SpaceX's planned Starship orbital test flights to Mars, search for the Saturday weather forecast for Boca Chica (Starbase, Texas), and determine if a launch simulation activity should be conducted indoors or outdoors assuming high wind or thunderstorm conditions are forecasted.",
    "G1": "Remember that the next cargo supply mission to the International Space Station (CRS-32) is scheduled for launch on 12 June 2026. Create a schedule log file named crs_schedule.txt in the sandbox.",
    "G2": "When is the CRS-32 supply mission scheduled to launch? Check your records and tell me.",
    "H": "Search for next-generation space telescopes planned for launch in the 2030s (such as LUVOIR, HabEx, or OST), fetch the top 3 detailed pages or URLs describing their designs, synthesise their primary scientific instruments, and output a beautifully structured numbered comparison of their primary mirror sizes and scientific goals."
}

CUSTOM_QUERIES = {
    "1": "Explain the technique that helps deep networks bypass layers using shortcut mapping to combat gradient problems without using the words ResNet or residual.",
    "2": "How can language models be aligned with human feedback using implicit reward equations and binary comparisons instead of reinforcement learning actor-critic policies, without using the words DPO or preference optimization?",
    "3": "In the ReAct paper, what was the exact success rate of the agent on the HotpotQA dataset compared to standard CoT and Acting-only baselines?",
    "4": "For GPT-3 175B adaptation, what is the exact number of trainable parameters and memory savings achieved by LoRA when rank r=4 is used?",
    "5": "What is the exact mathematical formula for Scaled Dot-Product Attention in the Transformer paper, and why is the scaling factor necessary?"
}

class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = io.StringIO()
        return self
    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        sys.stdout = self._stdout

async def run_query_and_save(key: str, query: str, filename_prefix: str, clear_memory: bool = False):
    print(f"🚀 Running Query {key}...")
    if clear_memory:
        _memory.clear()
        print("Cleared persistent memory.")

    # Capture stdout
    with Capturing() as output:
        try:
            await agent7.run(query)
        except Exception as e:
            print(f"\nERROR RUNNING QUERY: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
    
    # Save trace
    trace_text = "\n".join(output)
    trace_path = TRACES_DIR / f"{filename_prefix}_{key}.txt"
    trace_path.write_text(trace_text, encoding="utf-8")
    print(f"Saved trace to {trace_path}")
    
    # Print the FINAL answer preview to console
    final_lines = [l for l in output if l.startswith("FINAL:") or l.startswith("       ")]
    if final_lines:
        print("\n".join(final_lines[:5]))
    print("--------------------------------------------------\n")

async def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "base"
    
    if mode == "base":
        print("=== RUNNING EIGHT BASE QUERIES A-H ===")
        # Run standard & space queries verbatim
        # A, B need clean memory
        await run_query_and_save("A", BASE_QUERIES["A"], "base", clear_memory=True)
        await run_query_and_save("B", BASE_QUERIES["B"], "base", clear_memory=True)
        
        # C1 stores, C2 retrieves
        await run_query_and_save("C1", BASE_QUERIES["C1"], "base", clear_memory=True)
        await run_query_and_save("C2", BASE_QUERIES["C2"], "base", clear_memory=False)
        
        # D needs clean
        await run_query_and_save("D", BASE_QUERIES["D"], "base", clear_memory=True)
        
        # E, F need clean
        await run_query_and_save("E", BASE_QUERIES["E"], "base", clear_memory=True)
        await run_query_and_save("F", BASE_QUERIES["F"], "base", clear_memory=True)
        
        # G1 stores, G2 retrieves
        await run_query_and_save("G1", BASE_QUERIES["G1"], "base", clear_memory=True)
        await run_query_and_save("G2", BASE_QUERIES["G2"], "base", clear_memory=False)
        
        # H needs clean
        await run_query_and_save("H", BASE_QUERIES["H"], "base", clear_memory=True)
        
    elif mode == "custom_rag":
        print("=== RUNNING FIVE CUSTOM RAG QUERIES (INDEX ENABLED) ===")
        # We DO NOT clear memory between runs since we want the pre-indexed corpus to remain fully intact in memory!
        for k, q in CUSTOM_QUERIES.items():
            await run_query_and_save(k, q, "custom_rag", clear_memory=False)
            
    elif mode == "custom_norag":
        print("=== RUNNING FIVE CUSTOM NORAG QUERIES (INDEX DISABLED) ===")
        # To simulate "No-Corpus" we temporarily wipe the FAISS and memory json
        _memory.clear()
        print("Cleared persistent vector index and memory.json to simulate NO-CORPUS baseline.")
        for k, q in CUSTOM_QUERIES.items():
            await run_query_and_save(k, q, "custom_norag", clear_memory=False)

if __name__ == "__main__":
    asyncio.run(main())
