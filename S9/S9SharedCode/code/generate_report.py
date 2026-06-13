#!/usr/bin/env python3
import os
import sys
import json
import glob
import urllib.request
from pathlib import Path

def get_latest_session():
    sessions_dir = Path("state/sessions")
    if not sessions_dir.exists():
        print("Error: state/sessions directory does not exist.", file=sys.stderr)
        sys.exit(1)
    sessions = sorted(sessions_dir.glob("s8-*"), key=lambda p: p.stat().st_mtime)
    if not sessions:
        print("Error: No sessions found in state/sessions.", file=sys.stderr)
        sys.exit(1)
    return sessions[-1].name

def main():
    if len(sys.argv) > 1:
        session_id = sys.argv[1]
    else:
        session_id = get_latest_session()
        print(f"No session_id provided. Using latest session: {session_id}")

    session_path = Path("state/sessions") / session_id
    if not session_path.exists():
        print(f"Error: Session path {session_path} does not exist.", file=sys.stderr)
        sys.exit(1)

    # 1. Original user goal
    query_file = session_path / "query.txt"
    original_goal = query_file.read_text().strip() if query_file.exists() else "Unknown"

    # 2. Planner DAG
    graph_file = session_path / "graph.json"
    dag_description = "No graph.json available."
    if graph_file.exists():
        try:
            graph_data = json.loads(graph_file.read_text())
            nodes = graph_data.get("nodes", [])
            edges = graph_data.get("edges", [])
            
            dag_description = "```mermaid\ngraph TD\n"
            for node in nodes:
                nid = node.get("id")
                skill = node.get("skill")
                label = node.get("metadata", {}).get("label", skill)
                dag_description += f"    {nid}[\"{nid} ({skill})\"]\n"
            for edge in edges:
                dag_description += f"    {edge.get('source')} --> {edge.get('target')}\n"
            dag_description += "```"
        except Exception as e:
            dag_description = f"Error parsing graph.json: {e}"

    # Read all nodes in completion order
    node_files = sorted(
        (session_path / "nodes").glob("n_*.json"),
        key=lambda p: json.loads(p.read_text()).get("completed_at", 0)
    )

    node_states = []
    for f in node_files:
        try:
            node_states.append(json.loads(f.read_text()))
        except Exception:
            pass

    # 3. Browser path chosen, actions, screenshots, and extracted data
    browser_sections = []
    extracted_data = "No distilled data found."
    final_table = "No final comparison table found."

    for idx, st in enumerate(node_states, start=1):
        skill = st.get("skill")
        node_id = st.get("node_id")
        result = st.get("result", {})
        output = result.get("output", {})
        
        if skill == "browser" and result.get("success"):
            path = output.get("path", "Unknown")
            final_url = output.get("final_url", "Unknown")
            turns = output.get("turns", 0)
            actions = output.get("actions", [])
            
            # Find screenshots
            browser_dir = session_path / "browser"
            screenshots = []
            if browser_dir.exists():
                for turn_dir in sorted(browser_dir.glob("browser_*")):
                    for layer_dir in sorted(turn_dir.glob("*")):
                        if layer_dir.name == path:
                            for img in sorted(layer_dir.glob("turn_*_raw.png")):
                                rel_path = os.path.relpath(img, start=Path(".").resolve())
                                screenshots.append(rel_path)
            
            action_lines = []
            for act in actions:
                turn = act.get("turn")
                for sub_act in act.get("actions", []):
                    act_type = sub_act.get("type")
                    mark = sub_act.get("mark")
                    value = sub_act.get("value")
                    success = sub_act.get("success")
                    note = sub_act.get("note")
                    
                    if act_type == "click":
                        action_lines.append(f"- **Turn {turn}**: Clicked interactive element `#{mark}`")
                    elif act_type == "type":
                        action_lines.append(f"- **Turn {turn}**: Typed `\"{value}\"` into element `#{mark}`")
                    elif act_type == "key":
                        action_lines.append(f"- **Turn {turn}**: Pressed key `\"{value}\"`")
                    elif act_type == "scroll":
                        action_lines.append(f"- **Turn {turn}**: Scrolled {sub_act.get('direction')} by {sub_act.get('amount')}px")
                    elif act_type == "wait":
                        action_lines.append(f"- **Turn {turn}**: Waited {sub_act.get('seconds')}s")
                    elif act_type == "done":
                        action_lines.append(f"- **Turn {turn}**: Call complete (success={success}, note={note})")
            
            screenshot_lines = [f"- ![{os.path.basename(s)}](file://{os.path.abspath(s)})" for s in screenshots]
            
            action_text = "\n".join(action_lines) if action_lines else "- None"
            screenshot_text = "\n".join(screenshot_lines) if screenshot_lines else "- No screenshots captured"
            
            section = f"""### Node {node_id} (Goal: {st.get("metadata", {}).get("goal", "")[:100]}...)
- **Chosen Layer (Path)**: `{path}`
- **Final URL reached**: [{final_url}]({final_url})
- **Actions taken**:
{action_text}
- **Captured Screenshots**:
{screenshot_text}
"""
            browser_sections.append(section)
            
        elif skill == "distiller" and result.get("success"):
            fields = output.get("fields", {})
            extracted_data = "```json\n" + json.dumps(fields, indent=2) + "\n```"
            
        elif skill == "formatter" and result.get("success"):
            final_answer = output.get("final_answer", "")
            final_table = final_answer

    # 8. Cost summary
    cost_summary_text = "Gateway costs not available."
    try:
        url = f"http://localhost:8109/v1/cost/by_agent?session={session_id}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            cost_data = json.loads(response.read().decode())
            cost_summary_text = "```json\n" + json.dumps(cost_data, indent=2) + "\n```"
    except Exception as e:
        cost_summary_text = f"Could not retrieve cost ledger from gateway: {e}"

    browser_sections_text = "\n".join(browser_sections) if browser_sections else "No browser executions occurred."
    # Compile report
    report_content = f"""# S9 Browser-Capable Agent Replay Report
**Session ID**: `{session_id}`

---

## 1. Original User Goal
> {original_goal}

---

## 2. Planner DAG
Below is the execution flow generated by the Planner:

{dag_description}

---

## 3. Browser Paths and 4. Actions Taken
Here are the details of the browser-based executions during this run:

{browser_sections_text}

---

## 5. Page-State Logs
The page-state details (including accessibility tree logs or coordinate annotations) are stored in the local session folders:
- **Screenshots & Legends**: `state/sessions/{session_id}/browser/`

---

## 6. Extracted Data
The following data was extracted and structured by the `distiller` node:

{extracted_data}

---

## 7. Final Comparison Table
Here is the final output comparison table compiled by the `formatter` node:

{final_table}

---

## 8. Turn Count and Cost Summary
Below is the cost ledger breakdown retrieved directly from the LLM Gateway V9 pricing register:

{cost_summary_text}
"""

    report_path = Path("REPLAY_REPORT.md")
    report_path.write_text(report_content, encoding="utf-8")
    print(f"Report successfully compiled and written to: {report_path.resolve()}")

if __name__ == "__main__":
    main()
