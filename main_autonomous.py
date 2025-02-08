import re
import json
import random
import os
import time
import argparse
from datetime import datetime
from typing import Dict, Any

from memory.context_manager import ContextStorage
from tools.tool_manager import ToolManager
from providers.provider_library import ProviderLibrary
from prompts.system_prompts import SELECTED_PROMPT

# Add argument parsing
def parse_args():
    parser = argparse.ArgumentParser(description='Run autonomous agent with specified LLM provider')
    parser.add_argument('--provider', '-p', 
                       default='deepseek_ollama',
                       help='Name of the LLM provider to use (default: deepseek_ollama)')
    parser.add_argument('--list-providers', '-l',
                       action='store_true',
                       help='List available providers and exit')
    return parser.parse_args()

def detect_and_run_tools(response_text: str, tool_manager) -> str:
    pattern = r"TOOL_CALL:\s*\{.*?\}"
    
    def run_tool_call(match: re.Match) -> str:
        full_block = match.group(0)
        json_part = full_block[len("TOOL_CALL:"):].strip()
        try:
            call_data = json.loads(json_part)
        except json.JSONDecodeError as e:
            return f"[TOOL_CALL ERROR: invalid JSON => {e}]"

        if not isinstance(call_data, dict):
            return "[TOOL_CALL ERROR: top-level JSON must be an object]"
        if "tool" not in call_data or "input_schema" not in call_data:
            return "[TOOL_CALL ERROR: missing 'tool' or 'input_schema']"

        tool_name = call_data["tool"]
        tool_input = call_data["input_schema"]
        
        if tool_name not in tool_manager.tools:
            return f"[TOOL_CALL ERROR: tool '{tool_name}' not recognized]"

        tool_obj = tool_manager.tools[tool_name]
        try:
            result = tool_obj.run(tool_input)
            return f"[TOOL RESULT from '{tool_name}': {result.get('content','(no content)')}]"
        except Exception as ex:
            return f"[TOOL_CALL ERROR: tool '{tool_name}' threw => {ex}]"

    return re.sub(pattern, run_tool_call, response_text, flags=re.DOTALL)


class AutonomousAgent:
    def __init__(self, provider_name: str = 'deepseek_ollama'):
        self.context_storage = ContextStorage(storage_dir="memory/context_logs")
        
        # Initialize provider first
        provider_lib = ProviderLibrary()
        self.llm = provider_lib.get_provider(provider_name)
        if not self.llm:
            available = provider_lib.list_providers()
            raise ValueError(f"Provider '{provider_name}' not found. Available providers: {available}")
            
        # Pass provider to ToolManager
        self.tool_manager = ToolManager(register_defaults=True, llm_provider=self.llm)
        
        self.goal = "Create a file and write a message to it. Then read it back and print the message."
        self.session_id = "autonomous_session_01"
        self.running = True
        
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_file = os.path.join("memory", "context_logs", f"context_{timestamp_str}_{self.session_id}.txt")

    def run(self):
        while self.running:
            if not self.goal:
                self.goal = self._suggest_new_goal()

            last_context = self._get_rolling_context(self.log_file, lines=300)

            step_prompt = f"""
You are an autonomous agent. 
Current goal: {self.goal}.

Here is the recent context (last 300 lines of logs):
----------------------------------------
{last_context}
----------------------------------------

Plan your next step. You can call any tool if needed. 
If you've achieved your goal, test your system to ensure it's working as expected.
"""

            self.log("=== Next Step Prompt ===")
            self.log(step_prompt)

            # Call the LLM for a single response
            result = self.llm.run({
                "messages": [
                    {"content": SELECTED_PROMPT},
                    {"content": step_prompt}
                ]
            })

            response_content = result["content"]["content"]

            # Now parse for potential tool calls:
            final_text = detect_and_run_tools(response_content, self.tool_manager)

            self.log("\n--- Agent Response ---")
            self.log(final_text)

            # If the agent claims goal is achieved, pick a new one
            if "Goal Achieved" in final_text or "[GOAL_ACHIEVED]" in final_text:
                self.log("Goal has been marked achieved. Generating a new goal...\n")
                self.goal = self._suggest_new_goal()
                continue

            # Sleep a bit
            print("Sleeping for 5 seconds to avoid busy loop...")
            time.sleep(5)

    def _suggest_new_goal(self) -> str:
        suggestions = [
            "Improve internal memory documentation",
            "Find new ways to self-optimize and reduce token usage",
            "Investigate new data sources for knowledge updates",
            "Improve performance in tool usage",
            "Write low level AMD GPU driver packages to optimize GPU utilization for LLMs"
        ]
        return random.choice(suggestions)

    def log(self, message: str):
        print(message)
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(message + "\n")
        except Exception as e:
            print(f"[WARNING] Could not write to log file: {e}")

    def _get_rolling_context(self, filepath: str, lines: int = 20) -> str:
        if not os.path.exists(filepath):
            return ""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
            snippet = all_lines[-lines:] if len(all_lines) > lines else all_lines
            return "".join(snippet).strip()
        except Exception as e:
            return f"[ERROR reading log: {e}]"


if __name__ == "__main__":
    args = parse_args()
    provider_lib = ProviderLibrary()
    
    if args.list_providers:
        print("Available providers:")
        for provider in provider_lib.list_providers():
            print(f"  - {provider}")
        exit(0)
        
    try:
        agent = AutonomousAgent(provider_name=args.provider)
        agent.run()
    except ValueError as e:
        print(f"Error: {e}")
        exit(1)
