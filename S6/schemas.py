from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional, Literal

class Goal(BaseModel):
    id: str = Field(description="Unique identifier for the subgoal, e.g. goal_1, goal_2")
    description: str = Field(description="Description of the subgoal")
    status: Literal["open", "done"] = Field(default="open", description="Current status of the subgoal")
    attached_artifact_ids: List[str] = Field(default_factory=list, description="IDs of artifacts attached to this goal by Perception")

class PerceptionInput(BaseModel):
    user_query: str = Field(description="The primary user query")
    memory_hits: List[str] = Field(description="Factual context or action outcomes retrieved from memory")
    previous_goals: List[Goal] = Field(description="The list of subgoals from the previous iteration")
    previous_turns: List[Dict[str, Any]] = Field(description="A log of recent thoughts and actions in previous iterations")

class PerceptionOutput(BaseModel):
    reasoning: str = Field(description="Reasoning process for goal planning and state verification")
    goals: List[Goal] = Field(description="The updated list of decomposed subgoals with open/done status")

class DecisionInput(BaseModel):
    user_query: str = Field(description="The original user query")
    goals: List[Goal] = Field(description="The currently decomposed and updated goals from Perception")
    memory_hits: List[str] = Field(description="Relevant context or facts retrieved from memory")
    attached_artifact_contents: Dict[str, str] = Field(default_factory=dict, description="Artifact ID to its full text content, attached to the current active goal")
    conversation_history: List[Dict[str, Any]] = Field(description="History of assistant decisions and action outputs for the current session")

class DecisionOutput(BaseModel):
    reasoning: str = Field(description="Explanation of the planned next step or thinking process")
    action_type: Literal["tool", "answer"] = Field(description="Whether the decision is to call a tool or provide the final answer")
    tool_name: str = Field(default="", description="The name of the tool to invoke, if action_type is 'tool', or empty string '' if action_type is 'answer'")
    tool_args: Dict[str, Any] = Field(default_factory=dict, description="The arguments for the tool, if action_type is 'tool', or empty object {} if action_type is 'answer'")
    answer: str = Field(default="", description="The final answer to the user query, if action_type is 'answer', or empty string '' if action_type is 'tool'")

    @field_validator("tool_name", mode="before")
    @classmethod
    def clean_tool_name(cls, v):
        if v is None:
            return ""
        if isinstance(v, str):
            # Clean up trailing punctuation, quotes, commas, parentheses
            return v.strip().strip(",()\"'")
        return v

    @field_validator("answer", mode="before")
    @classmethod
    def convert_none_to_string(cls, v):
        if v is None:
            return ""
        return v

    @field_validator("tool_args", mode="before")
    @classmethod
    def convert_none_to_dict(cls, v):
        if v is None:
            return {}
        return v

class ActionInput(BaseModel):
    action_type: Literal["tool", "answer"] = Field(description="The type of action to execute")
    tool_name: Optional[str] = Field(default=None, description="The tool to call")
    tool_args: Optional[Dict[str, Any]] = Field(default=None, description="Arguments for the tool")
    answer: Optional[str] = Field(default=None, description="Final answer to return")

class ActionOutput(BaseModel):
    success: bool = Field(description="True if the action ran successfully")
    output: str = Field(description="Console output, summary of tool result, or final answer")
    artifact_id: Optional[str] = Field(default=None, description="The handle/ID of the generated artifact if output was large")
    error: Optional[str] = Field(default=None, description="Error message, if success is False")

class Fact(BaseModel):
    content: str = Field(description="The raw factual content stored")
    keywords: List[str] = Field(description="Lowercased keywords representing entities and dates for matching")
    timestamp: str = Field(description="ISO timestamp of when this fact was recorded")

class MemoryStore(BaseModel):
    facts: List[Fact] = Field(default_factory=list, description="durable list of persistent facts")
    actions: List[Dict[str, Any]] = Field(default_factory=list, description="history of action outcomes recorded in the session")
