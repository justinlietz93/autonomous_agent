import json
import os
import sys
from typing import Dict, Any, Optional, List
from openai import OpenAI
from dotenv import load_dotenv
from .tool_base import Tool
from datetime import datetime
from deepseek_goal_pursuit.prompts.system_prompts import create_system_prompt
from deepseek_goal_pursuit.core.context_storage import ContextStorage
import uuid
from deepseek_goal_pursuit.core.analysis_state import AnalysisState
import hashlib
from .config import settings
from deepseek_goal_pursuit.core.session_manager import SessionManager

class DeepseekToolWrapper:
    """
    A robust wrapper that handles multiple tool calls in streamed output.
    It accumulates text in a rolling buffer, detects 'TOOL_CALL:{...}',
    executes them, and logs the final results.
    """

    def __init__(self, model_provider=None):
        load_dotenv()
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )
        self.tools = {}
        self.last_tool_call = None
        self.last_result = None
        self.incomplete_call = ""  # Track partial JSON blocks
        self.model_provider = model_provider
        self.session_manager = SessionManager()
        self.context_storage = ContextStorage()
        
    def _select_provider(self):
        if settings.LLM_PROVIDER == "ollama":
            return self.tools["ollama_deepseek"]
        return self.tools["deepseek_api"]

    def _convert_schema_to_nl(self, schema: Dict) -> str:
        """Convert JSON schema to a concise bullet list."""
        lines = []
        props = schema.get("properties", {})
        required = schema.get("required", [])
        for name, info in props.items():
            desc = info.get("description", "No description")
            tpe = info.get("type", "any")
            req_flag = "*" if name in required else ""
            lines.append(f"- {name} ({tpe}{req_flag}): {desc}")
        return "\n".join(lines)

    def register_tool(self, tool: Tool):
        """
        Register a tool with a descriptive schema for the system prompt.
        """
        self.tools[tool.name] = tool

    def _create_system_prompt(self) -> str:
        """
        Build the system prompt with usage instructions + current token usage (optional).
        """
        tool_descriptions = []
        for name, tool in self.tools.items():
            tool_descriptions.append(f"""
Tool: {name}
Description: {tool.description}
Schema: {self._convert_schema_to_nl(tool.input_schema)}
""")
        
        return f"""You are an AI assistant with access to the following tools:

{''.join(tool_descriptions)}

When using a tool, format your response as:
TOOL_CALL:
{{
    "tool": "tool_name",
    "input": {{
        // tool parameters
    }}
}}

After each tool call, explain your reasoning and next steps.
"""

    def _track_tokens(self, text: str, is_input: bool = True) -> None:
        """
        Update input_tokens or output_tokens counters for the given text.
        """
        try:
            count = len(self.tokenizer.encode(text))
            if is_input:
                self.token_usage["input_tokens"] += count
            else:
                self.token_usage["output_tokens"] += count
        except Exception as e:
            print(f"[WARNING] Token tracking error: {e}")
            # fallback estimate
            approx = len(text) // 4
            if is_input:
                self.token_usage["input_tokens"] += approx
            else:
                self.token_usage["output_tokens"] += approx

    def _extract_calls_from_buffer(self, buffer: str) -> list:
        """
        Finds all complete 'TOOL_CALL:{...}' blocks in 'buffer'.
        For each call, store: {
          "raw": the entire substring including 'TOOL_CALL: ... }',
          "call": the parsed JSON dict
        }
        """
        found_calls = []
        search_pos = 0

        while True:
            tc_index = buffer.find("TOOL_CALL:", search_pos)
            if tc_index == -1:
                break  # no more calls

            brace_start = buffer.find('{', tc_index)
            if brace_start == -1:
                break

            brace_count = 0
            end_index = -1
            for i in range(brace_start, len(buffer)):
                if buffer[i] == '{':
                    brace_count += 1
                elif buffer[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_index = i + 1
                        break

            if end_index == -1:
                break  # incomplete JSON

            raw_sub = buffer[tc_index:end_index]
            json_str = buffer[brace_start:end_index]
            try:
                call_data = json.loads(json_str)
                # minimal shape check
                if isinstance(call_data, dict) and "tool" in call_data and "input_schema" in call_data:
                    found_calls.append({
                        "raw": raw_sub,
                        "call": call_data
                    })
            except json.JSONDecodeError:
                pass

            search_pos = end_index

        return found_calls

    def _call_hash(self, call_data: dict) -> str:
        """Create a unique hash for a tool call"""
        as_str = json.dumps(call_data, sort_keys=True)
        return hashlib.md5(as_str.encode('utf-8')).hexdigest()

    def execute(self, prompt: str) -> str:
        """Handle context inclusion and model execution."""
        # Context handling
        session_id = self.session_manager.session_id if hasattr(self, 'session_manager') else None
        if session_id and hasattr(self, 'context_storage'):
            context = self.context_storage.get_full_context(session_id)
            prompt = f"CONTEXT:\n{context}\n\nPROMPT:\n{prompt}"
        
        # Original execution logic
        messages = [{"role": "system", "content": self._create_system_prompt()},
                    {"role": "user", "content": prompt}]
        
        response = self.model_provider.run({"messages": messages, "temperature": 0.7})
        
        # Response parsing
        if isinstance(response, dict):
            return response.get("content", "") or response.get("response", "")
        return str(response)

    def _wrap_tool_result(self, result: Any) -> str:
        """
        Optional helper to add token usage metadata to a tool's result text.
        """
        result_str = str(result)
        self._track_tokens(result_str, is_input=False)
        total_used = self.token_usage["input_tokens"] + self.token_usage["output_tokens"]
        remaining = 64000 - total_used
        return (
            "[TOOL RESULT START]\n"
            f"{result_str}\n"
            f"[Token Impact] Total used: {total_used}, Remaining: {remaining}\n"
            "[TOOL RESULT END]\n"
        )
