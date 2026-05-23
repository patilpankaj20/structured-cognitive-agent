import secrets
import json
from pathlib import Path
from typing import Optional
from schemas import ActionInput, ActionOutput

# Threshold above which output is saved as an artifact
LARGE_OUTPUT_THRESHOLD = 5000

SANDBOX_DIR = Path(__file__).parent / "sandbox"
ARTIFACTS_DIR = SANDBOX_DIR / "artifacts"

class Action:
    def __init__(self):
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    async def execute(self, input_data: ActionInput, mcp_session) -> ActionOutput:
        """Executes a tool call via the active MCP session, or handles the final answer."""
        if input_data.action_type == "answer":
            return ActionOutput(
                success=True,
                output=input_data.answer or "Done."
            )

        if not input_data.tool_name:
            return ActionOutput(
                success=False,
                output="",
                error="Action type was 'tool' but no tool_name was provided."
            )

        tool_name = input_data.tool_name
        tool_args = input_data.tool_args or {}

        # print(f"[action] calling tool: {tool_name} with args: {tool_args}")

        try:
            # Dispatch tool call over MCP stdio session
            result = await mcp_session.call_tool(tool_name, tool_args)
            
            # Format output text from MCP result
            output_text = ""
            if result.content:
                # FastMCP wraps string output in TextContent
                output_text = getattr(result.content[0], "text", str(result.content[0]))
            
            if result.isError:
                return ActionOutput(
                    success=False,
                    output=output_text,
                    error=f"MCP tool returned an error: {output_text}"
                )

            # Check if output is extremely large
            if len(output_text) > LARGE_OUTPUT_THRESHOLD:
                # Generate unique hex ID (like art:09ff0a67fe264eb9)
                hex_id = secrets.token_hex(8)
                artifact_id = f"art:{hex_id}"
                
                # Save full contents to artifacts dir
                art_file = ARTIFACTS_DIR / f"{hex_id}.txt"
                art_file.write_text(output_text, encoding="utf-8")
                
                preview = output_text[:200].replace("\n", " ").strip()
                summary_output = f"[artifact {artifact_id}, {len(output_text)} bytes] preview: {preview}..."
                
                print(f"[action] Intercepted large output. Saved as {artifact_id} ({len(output_text)} bytes)")
                
                return ActionOutput(
                    success=True,
                    output=summary_output,
                    artifact_id=artifact_id
                )
            
            return ActionOutput(
                success=True,
                output=output_text
            )

        except Exception as e:
            return ActionOutput(
                success=False,
                output="",
                error=f"Exception during tool execution: {e}"
            )

    @staticmethod
    def load_artifact(artifact_id: str) -> Optional[str]:
        """Loads a saved artifact's text contents by its ID."""
        if not artifact_id.startswith("art:"):
            return None
        hex_id = artifact_id.split(":")[1]
        art_file = ARTIFACTS_DIR / f"{hex_id}.txt"
        if art_file.exists():
            return art_file.read_text(encoding="utf-8")
        return None
