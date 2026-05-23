#!/usr/bin/env python3
import asyncio
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Ensure schemas and cognitive modules are accessible
sys.path.insert(0, str(Path(__file__).parent))

from memory import Memory
from perception import Perception
from decision import Decision
from action import Action
from schemas import (
    Goal, PerceptionInput, PerceptionOutput,
    DecisionInput, DecisionOutput, ActionInput, ActionOutput
)

# MCP imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Define standard queries mapping to the 4 cognitive objectives:
# A: Artifact Attach Test, B: Multi-Goal + Memory Carryover, C: Durable Memory Across Two Runs, D: Multi-Source Synthesis
QUERIES = {
    "A": (
        "Fetch the Wikipedia page for Voyager 1 (https://en.wikipedia.org/wiki/Voyager_1) and tell me its "
        "launch date, its current estimated distance from Earth (in AU or km), and describe the three key "
        "components of the Golden Record carried on board."
    ),
    "B": (
        "Retrieve 3 primary mission objectives of SpaceX's planned Starship orbital test flights to Mars, "
        "search for the Saturday weather forecast for Boca Chica (Starbase, Texas), and determine if a launch "
        "simulation activity should be conducted indoors or outdoors assuming high wind or thunderstorm conditions are forecasted."
    ),
    "C1": (
        "Remember that the next cargo supply mission to the International Space Station (CRS-32) is scheduled "
        "for launch on 12 June 2026. Create a schedule log file named crs_schedule.txt in the sandbox."
    ),
    "C2": (
        "When is the CRS-32 supply mission scheduled to launch? Check your records and tell me."
    ),
    "D": (
        "Search for next-generation space telescopes planned for launch in the 2030s (such as LUVOIR, HabEx, or OST), "
        "fetch the top 3 detailed pages or URLs describing their designs, synthesise their primary scientific "
        "instruments, and output a beautifully structured numbered comparison of their primary mirror sizes and scientific goals."
    )
}

# ANSI color codes for premium visual logging
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_CYAN = "\033[36m"
C_GREEN = "\033[32m"
C_YELLOW = "\033[33m"
C_RED = "\033[31m"
C_MAGENTA = "\033[35m"

def log_header(title: str):
    print(f"\n{C_BOLD}{C_MAGENTA}" + "═" * 80 + f"{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}🌟 {title}{C_RESET}")
    print(f"{C_BOLD}{C_MAGENTA}" + "═" * 80 + f"{C_RESET}")

def log_turn_header(turn: int):
    print(f"\n{C_BOLD}{C_CYAN}┌" + "─" * 78 + f"┐{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}│ TURN {turn:<71} │{C_RESET}")
    print(f"{C_BOLD}{C_CYAN}└" + "─" * 78 + f"┘{C_RESET}")

async def run_agent(query_text: str, max_iterations: int = 10):
    log_header("LEO Session 6 Modular Cognitive Agent Loop")
    print(f"{C_BOLD}Query:{C_RESET} {query_text}\n")

    # Initialize state directory and memory
    memory = Memory()
    
    # Run the top-level memory classification / fact extraction first
    print(f"{C_CYAN}[memory] Checking for fact extraction...{C_RESET}")
    extracted_fact = memory.remember(query_text)
    if extracted_fact:
        print(f"{C_GREEN}✅ Memory extracted fact: \"{extracted_fact}\"{C_RESET}")
    else:
        print(f"{C_YELLOW}ℹ️ No new facts extracted to persistent memory.{C_RESET}")

    # Spawn mcp_server.py as a subprocess with stdio transport
    print(f"\n{C_CYAN}[mcp] Initializing Stdio MCP Server...{C_RESET}")
    mcp_params = StdioServerParameters(
        command=sys.executable,
        args=[str(Path(__file__).parent / "mcp_server.py")]
    )

    try:
        async with stdio_client(mcp_params) as (read, write):
            async with ClientSession(read, write) as session:
                print(f"{C_CYAN}[mcp] Initializing session...{C_RESET}")
                await session.initialize()
                
                # Fetch available tools and log
                mcp_tools = (await session.list_tools()).tools
                tools = [
                    {
                        "name": t.name,
                        "description": t.description or "",
                        "input_schema": t.inputSchema or {"type": "object", "properties": {}}
                    }
                    for t in mcp_tools
                ]
                print(f"{C_GREEN}✅ Connected to MCP Server. Available tools: {[t['name'] for t in tools]}{C_RESET}")

                # Core loops state
                perception = Perception()
                decision = Decision()
                action = Action()

                goals: List[Goal] = []
                previous_turns: List[Dict[str, Any]] = []
                conversation_history: List[Dict[str, Any]] = []

                turn_idx = 1
                final_answer = None
                should_stop = False

                while turn_idx <= max_iterations:
                    print(f"\n─── iter {turn_idx} ───")

                    # ── 1. MEMORY HIT LAYER ──
                    memory_hits = []
                    if not should_stop:
                        memory_hits = memory.read(query_text)
                        print(f"[memory.read]   {len(memory_hits)} hits")

                    # ── 2. PERCEPTION LAYER ──
                    perception_input = PerceptionInput(
                        user_query=query_text,
                        memory_hits=memory_hits,
                        previous_goals=goals,
                        previous_turns=previous_turns
                    )
                    perception_output = perception.process(perception_input)
                    goals = perception_output.goals
                    
                    # Print subgoals exactly in requested format
                    first_goal = True
                    for g in goals:
                        status_str = f"[{g.status}]"
                        goal_line = f"{status_str} {g.description}"
                        if first_goal:
                            print(f"[perception]    {goal_line}")
                            first_goal = False
                        else:
                            print(f"                {goal_line}")
                        if g.status == "open" and g.attached_artifact_ids:
                            attach_ids = ",".join(g.attached_artifact_ids)
                            print(f"                  attach={attach_ids}")

                    if should_stop:
                        print()
                        print(f"[done] all {len(goals)} goals satisfied")
                        break

                    # ── 3. ATTACHED ARTIFACTS LOADING ──
                    attached_artifact_contents = {}
                    for g in goals:
                        if g.status == "open":
                            if g.attached_artifact_ids:
                                for art_id in g.attached_artifact_ids:
                                    content = Action.load_artifact(art_id)
                                    if content is not None:
                                        if len(content) > 40000:
                                            content = content[:40000] + "\n\n[... content truncated for length ...]"
                                        attached_artifact_contents[art_id] = content
                                        print(f"[attach]        {art_id} ({len(content)} bytes)")
                            break

                    # ── 4. DECISION LAYER ──
                    decision_input = DecisionInput(
                        user_query=query_text,
                        goals=goals,
                        memory_hits=memory_hits,
                        attached_artifact_contents=attached_artifact_contents,
                        conversation_history=conversation_history
                    )
                    decision_output = decision.process(decision_input, tools)
                    
                    if decision_output.action_type == "tool":
                        import json
                        args_json = json.dumps(decision_output.tool_args)
                        print(f"[decision]      TOOL_CALL: {decision_output.tool_name}({args_json})")
                    else:
                        ans_preview = decision_output.answer.replace('\n', ' ')
                        if len(ans_preview) > 80:
                            ans_preview = ans_preview[:80] + "..."
                        print(f"[decision]      ANSWER: {ans_preview}")

                    # ── 5. ACTION LAYER ──
                    action_input = ActionInput(
                        action_type=decision_output.action_type,
                        tool_name=decision_output.tool_name,
                        tool_args=decision_output.tool_args,
                        answer=decision_output.answer
                    )
                    action_output = await action.execute(action_input, session)

                    if decision_output.action_type == "tool":
                        if action_output.success:
                            if action_output.artifact_id:
                                art_content = Action.load_artifact(action_output.artifact_id) or ""
                                print(f"[action]        → [artifact {action_output.artifact_id}, {len(art_content)} bytes] preview: ...")
                            else:
                                short_output = action_output.output.replace('\n', ' ')
                                if len(short_output) > 80:
                                    short_output = short_output[:80] + "..."
                                print(f"[action]        → {short_output}")
                        else:
                            print(f"[action]        → Error: {action_output.error}")
                    else:
                        if action_output.success:
                            final_answer = action_output.output
                            should_stop = True

                    # ── 6. RECORD ACTION OUTCOME & TURN HISTORY ──
                    action_summary = f"Turn {turn_idx}: reasoning='{decision_output.reasoning}' "
                    if decision_output.action_type == "tool":
                        action_summary += f"tool={decision_output.tool_name} success={action_output.success}"
                        if action_output.artifact_id:
                            action_summary += f" saved_as={action_output.artifact_id}"
                    else:
                        action_summary += f" answered"
                    
                    memory.record_action(decision_output.action_type, action_summary)

                    # Update history
                    conversation_history.append({
                        "role": "assistant",
                        "decision": decision_output.model_dump(),
                    })
                    conversation_history.append({
                        "role": "user",
                        "action_output": action_output.model_dump()
                    })

                    previous_turns.append({
                        "turn": turn_idx,
                        "reasoning": perception_output.reasoning,
                        "goals": [g.model_dump() for g in goals],
                        "decision": decision_output.model_dump(),
                        "action_output": action_output.model_dump()
                    })

                    turn_idx += 1

                # ── 7. EXECUTION SUMMARY ──
                if final_answer:
                    final_answer = final_answer.replace('\\n', '\n')
                    lines = final_answer.strip().split('\n')
                    if lines:
                        print(f"\nFINAL: {lines[0]}")
                        for line in lines[1:]:
                            print(f"       {line}")
                print()
                return final_answer, turn_idx

    except Exception as e:
        print(f"\n{C_RED}CRITICAL: Stdio MCP Server failed or client crashed: {e}{C_RESET}")
        import traceback
        traceback.print_exc()
        raise e

def main():
    parser = argparse.ArgumentParser(description="Session 6 Cognitive Agent Orchestration Script")
    parser.add_argument(
        "--query",
        choices=["A", "B", "C1", "C2", "D"],
        help="Select a predefined query (A: Shannon Wikipedia, B: Tokyo, C1: Mom birthday run 1, C2: Mom birthday run 2, D: Asyncio)"
    )
    parser.add_argument(
        "--prompt",
        type=str,
        help="Provide a custom user prompt directly"
    )
    parser.add_argument(
        "--clear-memory",
        action="store_true",
        help="Clear persistent memory before running"
    )
    
    args = parser.parse_args()

    if args.clear_memory:
        m = Memory()
        m.clear()
        print("🧹 Persistent memory successfully cleared.")
        if not args.query and not args.prompt:
            return

    # Choose query text
    query_text = ""
    if args.query:
        query_text = QUERIES[args.query]
    elif args.prompt:
        query_text = args.prompt
    else:
        parser.print_help()
        sys.exit(0)

    # Run the event loop
    asyncio.run(run_agent(query_text))

if __name__ == "__main__":
    main()
