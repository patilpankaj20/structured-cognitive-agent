import sys
from pathlib import Path
from typing import List, Dict, Any
from schemas import DecisionInput, DecisionOutput

# Import V3 LLM Client
sys.path.insert(0, str(Path(__file__).parent / "llm_gatewayV3"))
from client import LLM

class Decision:
    def __init__(self):
        self.llm = LLM()

    def process(self, input_data: DecisionInput, tools: List[Dict[str, Any]]) -> DecisionOutput:
        """Determines the next cognitive action (tool call or final answer)."""
        schema = DecisionOutput.model_json_schema()

        # Build tools description string
        tools_block = ""
        for t in tools:
            props = t.get("input_schema", {}).get("properties", {}) or {}
            params = ", ".join(f"{k}: {v.get('type', 'any')}" for k, v in props.items())
            tools_block += f"- {t['name']}({params}) — {t.get('description', '')}\n"

        system_prompt = (
            "You are the Decision layer of a modular cognitive agent. Your task is to decide the single best next action "
            "to make progress toward achieving the open subgoals.\n\n"
            "You can choose to:\n"
            "1. Call an MCP tool to gather information or manipulate state.\n"
            "2. Provide the final answer to the user query if all subgoals are completed or you have all necessary information.\n\n"
            "Rules:\n"
            "- Study the conversation history carefully. Do not make duplicate tool calls or repeat failed actions.\n"
            "- Reuse results from earlier turns instead of re-fetching or re-calculating.\n"
            "- Read any attached artifact contents loaded for you. Use them to extract information or synthesise answers.\n"
            "- If a tool call returned an artifact handle like 'art:<hex>', note that the full text content is available to you "
            "in the attached_artifact_contents when that goal is active.\n"
            "- Always specify your reasoning, and then output either action_type='tool' (with tool_name and tool_args) or action_type='answer' (with answer).\n\n"
            "CRITICAL TOOL CALL RULES:\n"
            "- The 'tool_name' field MUST be exactly the clean string name of the tool (e.g. 'web_search', 'fetch_url', 'create_file').\n"
            "- Do NOT include arguments, commas, parentheses, or signatures inside the 'tool_name' field itself.\n"
            "- ALL tool arguments MUST be provided within the 'tool_args' dictionary.\n\n"
            f"Available tools from MCP server:\n{tools_block}\n\n"
            "CRITICAL SCHEMA COMPLIANCE:\n"
            "You must respond in valid JSON format matching the schema perfectly.\n"
            "You MUST include all five properties in your JSON response: 'reasoning', 'action_type', 'tool_name', 'tool_args', and 'answer'.\n"
            "- If action_type is 'tool': 'tool_name' must be the tool's string name, 'tool_args' must be the arguments object, and 'answer' MUST be an empty string \"\".\n"
            "- If action_type is 'answer': 'tool_name' MUST be an empty string \"\", 'tool_args' MUST be an empty object {}, and 'answer' must be the final answer string."
        )

        # Format attached artifacts cleanly using structured fences
        artifacts_block = ""
        for art_id, content in (input_data.attached_artifact_contents or {}).items():
            artifacts_block += f"=== START ARTIFACT {art_id} ===\n{content}\n=== END ARTIFACT {art_id} ===\n\n"
        if not artifacts_block:
            artifacts_block = "(No attached artifacts)\n"

        prompt = (
            f"User query: {input_data.user_query}\n\n"
            f"Current Goals State:\n{[g.model_dump() for g in input_data.goals]}\n\n"
            f"Memory Hits:\n{input_data.memory_hits}\n\n"
            f"Attached Artifacts Contents:\n{artifacts_block}"
            f"Conversation History:\n{input_data.conversation_history}"
        )

        try:
            reply = self.llm.chat(
                prompt=prompt,
                system=system_prompt,
                response_format={
                    "type": "json_object",
                },
                provider="gemini",
                temperature=0,
            )

            import json
            reply_text = reply.get("text", "").strip()
            # Clean up potential markdown wrapper
            if reply_text.startswith("```json"):
                reply_text = reply_text[7:]
            if reply_text.endswith("```"):
                reply_text = reply_text[:-3]
            reply_text = reply_text.strip()
            
            parsed_data = json.loads(reply_text)
            return DecisionOutput.model_validate(parsed_data)
        except Exception as e:
            import httpx
            if isinstance(e, httpx.HTTPStatusError):
                print(f"[decision] Warning: LLM call failed. Status: {e.response.status_code}. Response: {e.response.text}")
            else:
                print(f"[decision] Warning: LLM call failed or parsed incorrectly: {e}")

        # Fallback decision
        return DecisionOutput(
            reasoning="Fallback due to LLM error",
            action_type="answer",
            tool_name="",
            tool_args={},
            answer="I encountered an issue making a decision. Please try again."
        )
