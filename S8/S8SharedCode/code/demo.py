#!/usr/bin/env python3
"""Interactive demo runner for Session 8.

Allows the user to easily launch predefined test cases, verify specific multi-agent features
(concurrency, recovery splices, custom skills, checkpoint resume), clear memories, and run
session replays.
"""

from __future__ import annotations

import os
import re
import sys
import time
import signal
import subprocess
from pathlib import Path

# ANSI colors for premium styling
C_BLUE = "\033[94m"
C_CYAN = "\033[96m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_RED = "\033[91m"
C_BOLD = "\033[1m"
C_RESET = "\033[0m"

DEMO_CASES = {
    "1": {
        "title": "Hello World Query (Simple 2-node graph)",
        "query": "Say hello in one short sentence.",
        "concept": "Demonstrates the simplest possible 2-node DAG: planner -> formatter. Quick serialization check.",
    },
    "2": {
        "title": "Claude Shannon biography (Deep research)",
        "query": "Fetch https://en.wikipedia.org/wiki/Claude_Shannon and tell me his birth date, death date, and three key contributions to information theory.",
        "concept": "Demonstrates sequential dependencies where the researcher utilizes fetch_url, passes output to distiller, and formatter compiles final biography.",
    },
    "3": {
        "title": "Parallel Populations search (Concurrency check)",
        "query": "What are the populations of London, Paris, and Berlin? Compare them.",
        "concept": "Planner seeds 3 parallel researcher tasks. Executes concurrently, scaling to max(branches) wall-clock time.",
    },
    "4": {
        "title": "Coder Skill & Sandbox execution (Math calculate)",
        "query": "Calculate the sum of the square roots of the first 50 odd numbers.",
        "concept": "Coder skill outputs code in clean JSON format. Static graph edges automatically route output to sandbox_executor.",
    },
    "5": {
        "title": "Python Crash & Recovery splice",
        "query": "Write a python script to open a nonexistent file and do not catch the error",
        "concept": "Sandbox returns exit code -1 on crash. The orchestrator catches the failure and dynamically splices recovery planner to resolve.",
    },
    "6": {
        "title": "SIGKILL Interrupt & Resume Simulation",
        "query": "populations of London, Paris, Berlin; which two are closest?",
        "concept": "Spawns execution in background, SIGKILLs it mid-run, then allows you to resume exactly where it was cut off.",
        "special": True,
    },
    "7": {
        "title": "Critic Failure Loop (Safety node capping)",
        "query": "Extract list of fruits from: 'apples, bananas, oranges, cherries' and verify there are exactly 3 fruits.",
        "concept": "Distiller extracts 4 items. Critic fails it because rule requires 3. Recovery loops until node count limit (60) is reached.",
    },
    "8": {
        "title": "Custom Text Analyst Skill",
        "query": "Use the text_analyst skill to analyze the word count metrics of this text: 'The quick brown fox jumps over the lazy dog.'",
        "concept": "Verifies custom skill text_analyst parses text and yields structured metrics in a custom YAML-registered workflow.",
    },
}

S7_CASES = {
    "1": {
        "title": "SpaceX Mars Starship Launch Simulation",
        "query": "Retrieve 3 primary mission objectives of SpaceX's planned Starship orbital test flights to Mars, search for the Saturday weather forecast for Boca Chica (Starbase, Texas), and determine if a launch simulation activity should be conducted indoors or outdoors assuming high wind or thunderstorm conditions are forecasted.",
        "concept": "Executes SpaceX objectives search and Boca Chica weather forecast in parallel (S8 concurrency), then synthesized by formatter.",
    },
    "2": {
        "title": "Space Telescopes comparison (2030s plans)",
        "query": "Search for next-generation space telescopes planned for launch in the 2030s (such as LUVOIR, HabEx, or OST), fetch the top 3 detailed pages or URLs describing their designs, synthesise their primary scientific instruments, and output a beautifully structured numbered comparison of their primary mirror sizes and scientific goals.",
        "concept": "Planner schedules parallel search queries for space telescopes, fetching and comparing them concurrently in S8.",
    },
    "3": {
        "title": "Voyager 1 biography & distance",
        "query": "Fetch the Wikipedia page for Voyager 1 (https://en.wikipedia.org/wiki/Voyager_1) and tell me its launch date, its current estimated distance from Earth (in AU or km), and describe the three key components of the Golden Record carried on board.",
        "concept": "Deep retrieval flow using wikipedia URL parsing and summary synthesis.",
    },
    "4": {
        "title": "ResNet Technique (Shortcut mapping)",
        "query": "Explain the technique that helps deep networks bypass layers using shortcut mapping to combat gradient problems without using the words ResNet or residual.",
        "concept": "Requires retrieval / web search synthesis on advanced neural network architectures under constraint validation.",
    },
    "5": {
        "title": "DPO Reward Alignment (Implicit reward)",
        "query": "How can language models be aligned with human feedback using implicit reward equations and binary comparisons instead of reinforcement learning actor-critic policies, without using the words DPO or preference optimization?",
        "concept": "Requires searching literature for Direct Preference Optimization and describing it under strict vocabulary constraints.",
    }
}

def print_header(title: str) -> None:
    print(f"\n{C_BLUE}{C_BOLD}{'═' * 65}")
    print(f" {title.center(63)}")
    print(f"{'═' * 65}{C_RESET}")

def run_cmd(args: list[str]) -> subprocess.CompletedProcess | None:
    """Helper to run a process and stream output to terminal."""
    try:
        # Use uv run python to invoke
        proc = subprocess.run(
            ["uv", "run", "python"] + args,
            stdout=sys.stdout,
            stderr=sys.stderr,
            text=True
        )
        return proc
    except KeyboardInterrupt:
        print(f"\n{C_RED}[Interrupt] Command aborted by user.{C_RESET}")
        return None

def clear_memory() -> None:
    print(f"\n{C_YELLOW}Wiping memory databases (FAISS + memory.json)...{C_RESET}")
    run_cmd(["-c", "import memory; memory.clear()"])
    print(f"{C_GREEN}Memory cleared. All agent queries will execute live web searches.{C_RESET}")

def run_sigkill_scenario() -> None:
    print_header("SIGKILL Interrupt & Resume Simulation")
    print(f"{C_CYAN}Concept: {DEMO_CASES['6']['concept']}{C_RESET}\n")
    print(f"Starting query in subprocess: {C_BOLD}{DEMO_CASES['6']['query']}{C_RESET}")
    print(f"{C_YELLOW}Memory will be cleared first to ensure search takes a few seconds...{C_RESET}")
    run_cmd(["-c", "import memory; memory.clear()"])
    
    # Launch flow.py as a subprocess with stdout pipe so we can scan for Session ID
    p = subprocess.Popen(
        ["uv", "run", "python", "flow.py", DEMO_CASES["6"]["query"]],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    sid = None
    print(f"\n{C_YELLOW}--- Spawning Subprocess (PID: {p.pid}) ---{C_RESET}")
    
    try:
        # Read output line by line, print it, and extract Session ID
        for line in p.stdout:
            print(line, end="")
            # Check for: session s8-xxxxxxxx
            m = re.search(r"session\s+(s8-[a-f0-9]+)", line)
            if m:
                sid = m.group(1)
                print(f"\n{C_GREEN}[Detected Session ID: {sid}]{C_RESET}")
                print(f"{C_YELLOW}Waiting 4 seconds for parallel research to spawn, then killing...{C_RESET}")
                time.sleep(4.0)
                print(f"\n{C_RED}[KILLING] Sending SIGKILL to process {p.pid}...{C_RESET}")
                p.send_signal(signal.SIGKILL)
                break
    except Exception as e:
        print(f"\n{C_RED}Error: {e}{C_RESET}")
        p.kill()
        
    p.wait()
    print(f"{C_RED}Subprocess terminated with SIGKILL.{C_RESET}\n")
    
    if not sid:
        print(f"{C_RED}Could not extract Session ID. Please run flow.py manually to test resume.{C_RESET}")
        return
        
    print(f"{C_CYAN}Atomic graph checkpoint saved at: {C_BOLD}state/sessions/{sid}/graph.json{C_RESET}")
    print(f"You can now resume this execution. Press enter to run resume command:")
    print(f"{C_GREEN}{C_BOLD}uv run python flow.py --resume {sid}{C_RESET}")
    input("> ")
    
    print_header(f"Resuming Session {sid}")
    run_cmd(["flow.py", "--resume", sid])

def run_replay() -> None:
    print_header("Session Replay Dashboard")
    # First list available sessions
    run_cmd(["replay.py"])
    print(f"\n{C_CYAN}Enter a Session ID from above to replay node-by-node, or press enter to go back:{C_RESET}")
    sid = input("> ").strip()
    if sid:
        run_cmd(["replay.py", sid])

def run_s7_submenu(s7_only: bool = False) -> None:
    while True:
        print_header("Session 7 Core Showcase Examples")
        print(f"{C_BOLD}Select a Session 7 example to run under the S8 orchestrator:{C_RESET}\n")
        
        for key, case in S7_CASES.items():
            print(f"  {C_CYAN}{key}){C_RESET} {C_BOLD}{case['title']}{C_RESET}")
            print(f"     {C_YELLOW}↳ Query: {case['query'][:100]}...{C_RESET}")
            print(f"     {C_BLUE}↳ Concept: {case['concept']}{C_RESET}")
            
        back_text = "Quit" if s7_only else "Go back to main menu"
        print(f"\n  {C_CYAN}B){C_RESET} {C_BOLD}{back_text}{C_RESET}")
        
        print(f"\n{C_CYAN}Choice:{C_RESET} ", end="")
        choice = input().strip().lower()
        
        if choice == "b":
            break
        elif choice in S7_CASES:
            case = S7_CASES[choice]
            print_header(case["title"])
            print(f"{C_CYAN}Concept: {case['concept']}{C_RESET}")
            print(f"Query: {C_BOLD}{case['query']}{C_RESET}\n")
            
            # For space search / parallel queries, clear memory to force live concurrency
            if choice in ("1", "2"):
                print(f"{C_YELLOW}Note: Memory was cleared to showcase live concurrent research branches.{C_RESET}")
                run_cmd(["-c", "import memory; memory.clear()"])
                
            print(f"Executing: {C_GREEN}uv run python flow.py \"{case['query']}\"{C_RESET}\n")
            run_cmd(["flow.py", case["query"]])
            
            print("\nPress enter to return to the Session 7 submenu...")
            input()
        else:
            print(f"\n{C_RED}Invalid choice. Please try again.{C_RESET}")
            time.sleep(1)

def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] in ("--s7", "--s7-only", "s7"):
        run_s7_submenu(s7_only=True)
        return

    while True:
        print_header("Session 8 Growing-Graph Orchestrator Demo")
        print(f"{C_BOLD}Select a scenario to run:{C_RESET}\n")
        
        # List options
        for key, case in DEMO_CASES.items():
            print(f"  {C_CYAN}{key}){C_RESET} {C_BOLD}{case['title']}{C_RESET}")
            print(f"     {C_YELLOW}↳ {case['concept']}{C_RESET}")
            
        print(f"\n  {C_CYAN}S7){C_RESET} {C_BOLD}Session 7 Core Showcase Examples (Submenu){C_RESET}")
        print(f"  {C_CYAN}R){C_RESET} {C_BOLD}Replay a past session node-by-node{C_RESET}")
        print(f"  {C_CYAN}C){C_RESET} {C_BOLD}Clear Memory databases{C_RESET}")
        print(f"  {C_CYAN}Q){C_RESET} {C_BOLD}Quit{C_RESET}")
        
        print(f"\n{C_CYAN}Choice:{C_RESET} ", end="")
        choice = input().strip().lower()
        
        if choice == "q":
            print(f"\n{C_GREEN}Goodbye!{C_RESET}\n")
            break
        elif choice == "c":
            clear_memory()
            print("\nPress enter to continue...")
            input()
        elif choice == "r":
            run_replay()
            print("\nPress enter to continue...")
            input()
        elif choice == "s7":
            run_s7_submenu()
        elif choice in DEMO_CASES:
            case = DEMO_CASES[choice]
            if case.get("special"):
                run_sigkill_scenario()
            else:
                print_header(case["title"])
                print(f"{C_CYAN}Concept: {case['concept']}{C_RESET}")
                print(f"Query: {C_BOLD}{case['query']}{C_RESET}\n")
                
                # Check if memory should be cleared for population search to avoid memory caching bypass
                if choice in ("3", "7"):
                    print(f"{C_YELLOW}Note: Memory was cleared to showcase live execution features.{C_RESET}")
                    run_cmd(["-c", "import memory; memory.clear()"])
                    
                print(f"Executing: {C_GREEN}uv run python flow.py \"{case['query']}\"{C_RESET}\n")
                run_cmd(["flow.py", case["query"]])
                
            print("\nPress enter to return to the menu...")
            input()
        else:
            print(f"\n{C_RED}Invalid choice. Please try again.{C_RESET}")
            time.sleep(1)

if __name__ == "__main__":
    # Ensure executable permission is set if run directly, or execute via python
    main()
