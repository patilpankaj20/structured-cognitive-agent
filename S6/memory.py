import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from schemas import Fact, MemoryStore

# Path to the persistent memory file
STATE_DIR = Path(__file__).parent / "state"
MEMORY_FILE = STATE_DIR / "memory.json"

# Import V3 LLM Client
sys.path.insert(0, str(Path(__file__).parent / "llm_gatewayV3"))
from client import LLM

class FactExtraction(BaseModel):
    is_new_fact: bool = Field(description="True if the prompt contains a personal fact or piece of information that the user explicitly wants remembered.")
    fact_content: str = Field(default="", description="The extracted clean fact statement, e.g. 'Mom's birthday is on 15 May 2026'")
    keywords: List[str] = Field(default_factory=list, description="A list of 3-5 lowercase keywords representing entities or dates, e.g. ['mom', 'birthday', 'may', '2026']")

    @field_validator("fact_content", mode="before")
    @classmethod
    def convert_none_to_string(cls, v):
        if v is None:
            return ""
        return v

class Memory:
    def __init__(self):
        STATE_DIR.mkdir(exist_ok=True)
        self.store = self._load_store()
        # Clear actions on startup since we are beginning a new session run!
        self.store.actions = []
        self.save()

    def _load_store(self) -> MemoryStore:
        if not MEMORY_FILE.exists():
            return MemoryStore()
        try:
            content = MEMORY_FILE.read_text(encoding="utf-8")
            data = json.loads(content)
            return MemoryStore.model_validate(data)
        except Exception:
            return MemoryStore()

    def save(self) -> None:
        MEMORY_FILE.write_text(self.store.model_dump_json(indent=2), encoding="utf-8")

    def clear(self) -> None:
        """Clear memory for assignment reset attempts."""
        self.store = MemoryStore()
        self.save()

    def remember(self, prompt: str) -> Optional[str]:
        """Classify and extract facts from the user prompt at the very top of the run.
        Uses structured output via LLM Gateway V3.
        """
        # Stopwords or queries shouldn't trigger fact storage.
        # Use LLM Gateway V3 perception tier to evaluate.
        llm = LLM()
        schema = FactExtraction.model_json_schema()
        
        system_prompt = (
            "You are a memory classification assistant. Analyze the user's prompt. "
            "If the user is sharing a personal fact (e.g. birth dates, event dates, preferences) "
            "and wants it remembered, extract the fact and 3-5 lowercased keywords. "
            "Otherwise, output is_new_fact as false.\n\n"
            "CRITICAL SCHEMA COMPLIANCE:\n"
            "You must respond in valid JSON format matching the schema perfectly.\n"
            "You MUST include all three properties in your JSON response: 'is_new_fact', 'fact_content', and 'keywords'.\n"
            "- If is_new_fact is True: 'fact_content' must be the extracted fact string, and 'keywords' must be a list of 3-5 lowercase keywords.\n"
            "- If is_new_fact is False: 'fact_content' MUST be an empty string \"\", and 'keywords' MUST be an empty array []."
        )
        
        try:
            reply = llm.chat(
                prompt=f"User prompt: \"{prompt}\"",
                system=system_prompt,
                response_format={
                    "type": "json_schema",
                    "schema": schema,
                    "name": "FactExtraction",
                    "strict": True,
                },
                provider="gemini",
                temperature=0,
            )
            
            if reply.get("parsed"):
                extraction = FactExtraction.model_validate(reply["parsed"])
                if extraction.is_new_fact and extraction.fact_content:
                    # Save to store
                    fact = Fact(
                        content=extraction.fact_content,
                        keywords=[k.lower() for k in extraction.keywords],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    # Check if already exists to avoid duplication
                    if not any(f.content.lower() == fact.content.lower() for f in self.store.facts):
                        self.store.facts.append(fact)
                        self.save()
                        print(f"[memory.remember] classified and saved fact: \"{fact.content}\"")
                    return fact.content
        except Exception as e:
            print(f"[memory.remember] Warning: Fact extraction LLM call failed: {e}")
        return None

    def record_action(self, action_type: str, action_summary: str) -> None:
        """Record the outcome of an action into the session's action history."""
        self.store.actions.append({
            "type": action_type,
            "summary": action_summary,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.save()

    def read(self, query: str) -> List[str]:
        """Query memory using keyword intersection matching.
        Returns a list of matching persistent facts and action outputs.
        """
        # Tokenize query to find keywords
        query_words = set(query.lower().replace("?", "").replace(".", "").replace(",", "").split())
        stopwords = {"is", "a", "the", "on", "to", "in", "for", "of", "and", "or", "what", "when", "how", "where", "tell", "me", "find", "check"}
        query_keywords = query_words - stopwords

        hits = []

        # 1. Match against persistent facts
        for fact in self.store.facts:
            # Check if there's any keyword intersection
            fact_keywords = set(fact.keywords)
            # Match on clean tokens of content too, in case keywords missed
            fact_content_tokens = set(fact.content.lower().replace(".", "").replace(",", "").split())
            combined_fact_set = fact_keywords | fact_content_tokens
            
            if query_keywords & combined_fact_set:
                hits.append(f"Fact: {fact.content}")

        # 2. Add recent action outcomes if relevant
        # To avoid spamming, we add the latest actions.
        for act in reversed(self.store.actions[-5:]):
            # Check if any query keyword is in the action summary
            act_words = set(act["summary"].lower().split())
            if query_keywords & act_words or not query_keywords:
                hits.append(f"Action Outcome ({act['type']}): {act['summary']}")

        return hits
