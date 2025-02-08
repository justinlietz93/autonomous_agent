import re
import json
import random
import os
import time
import argparse
import sys
from datetime import datetime
from typing import Dict, Any
import string  # Add to imports at top

from memory.context_manager import ContextStorage
from tools.tool_manager import ToolManager
from providers.provider_library import ProviderLibrary
from providers.create_ollama_provider import create_provider
from prompts.prompt_manager import PromptManager
from tools.tool_parser import RealTimeToolParser, ToolCallError


# Update argument parsing
def parse_args():
    parser = argparse.ArgumentParser(description='Run autonomous agent with specified LLM provider')
    parser.add_argument('--provider', '-p', 
                       default='deepseek_ollama',
                       help='Name of the LLM provider to use (default: deepseek_ollama)')
    parser.add_argument('--list-providers', '-l',
                       action='store_true',
                       help='List available providers and exit')
    parser.add_argument('--new-provider', type=str, 
                       help="Create new Ollama provider using Ollama name(e.g. qwen2.5-coder)")
    parser.add_argument('--prompt', type=str,
                       help="Name of the prompt to use (e.g. SELF_OPTIMIZATION)")
    parser.add_argument('--list-prompts',
                       action='store_true',
                       help='List available prompts and exit')
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
            
        # Initialize prompt manager early
        self.prompt_manager = PromptManager(model_name=provider_name)
        
        # Pass provider to ToolManager
        self.tool_manager = ToolManager(register_defaults=True, llm_provider=self.llm)
        
        self.goal = "FOLLOW ALL INSTRUCTIONS EXPLICITLY. FORMAT TOOL CALLS CORRECTLY."
        
        # Generate random session ID with prompt name
        random_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        prompt_name = self.prompt_manager.active_prompt.lower()
        self.session_id = f"{prompt_name}_{random_chars}"
        
        self.running = True
        
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_file = os.path.join("memory", "context_logs", f"context_{timestamp_str}_{self.session_id}.txt")

    def run(self):
        """
        Run the autonomous loop indefinitely, processing responses
        and avoiding repeated identical responses in a row.
        """
        last_response = ""
        repeat_count = 0

        while self.running:
            if not self.goal:
                self.goal = self._suggest_new_goal()

            last_context = self._get_rolling_context(self.log_file, lines=50)

            step_prompt = f"""
Current goal: {self.goal}.

Here is some context from your previous session (last 50 lines of logs):
----------------------------------------
{last_context}
----------------------------------------
End of previous context.
----------------------------------------

Immediately continue where you left off. 
Do not stop until you have achieved your goal.
You will have amnesia at the beginning of each session, so you must review the provided context 
and use it to achieve your goal. You can also use tools to read the context files to refresh your memory.
You should try to get as much as possible done in each session, even when you think you're done you must
be even more thorough and quality oriented. You should run indefinitely.

The main prompts do not know how far you've made it into your goal, so don't assume you're starting
from scratch.
"""

            self.log("=== Next Step Prompt ===")
            self.log(step_prompt)

            # Call the LLM for a single response
            result = self.llm.run({
                "messages": [
                    {"content": self.prompt_manager.get_full_prompt()},
                    {"content": step_prompt}
                ]
            })

            response_content = result["content"]["content"]

            # Check for repeated response

            if response_content == last_response:
                repeat_count += 1
            else:
                repeat_count = 0

            if repeat_count >= 2:
                # If we've repeated the exact same response multiple times,
                # we add a small note to the LLM prompt to encourage a different result.
                self.log("\n[NOTICE: LLM repeated same response multiple times. Adding note to break repetition.]\n")
                response_content += "\n(LLM: Please provide new content, not the same as before.)"


            # Now parse for potential tool calls:
            final_text = detect_and_run_tools(response_content, self.tool_manager)

            self.log("\n--- Your Previous Response ---")
            self.log(final_text)

            # Sleep a bit
            print("Sleeping for 3 seconds to avoid busy loop...")
            time.sleep(3)

    def _suggest_new_goal(self) -> str:
        suggestions = [
            "Manually write a new prompt for yourself in the prompts folder and set that as the default prompt."
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
    
    # Handle provider creation
    if args.new_provider:
        create_provider(args.new_provider)
        provider_name = f"{args.new_provider}_ollama"
        print(f"Provider '{args.new_provider}' created successfully.")
        print(f"You can now use it by specifying the provider name in the command line.")
        print(f"Example: python main_autonomous.py --provider {provider_name}")
        sys.exit(0)
        
    # Handle prompt listing
    if args.list_prompts:
        prompt_manager = PromptManager()
        print("Available prompts:")
        for prompt in prompt_manager.list_prompts():
            print(f"  - {prompt}")
        exit(0)
        
    # Handle provider listing
    if args.list_providers:
        print("Available providers:")
        provider_lib = ProviderLibrary()
        for provider in provider_lib.list_providers():
            print(f"  - {provider}")
        exit(0)
        
    try:
        agent = AutonomousAgent(provider_name=args.provider)
        if args.prompt:
            agent.prompt_manager.set_active_prompt(args.prompt)
        agent.run()
    except ValueError as e:
        print(f"Error: {e}")
        exit(1)
