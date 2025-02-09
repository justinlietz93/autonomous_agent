from asyncio.log import logger
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
from tools.parse_formatter import InlineCallParser
from tools.tool_manager import ToolManager
from providers.provider_library import ProviderLibrary
from prompts.prompt_manager import PromptManager
from tools.tool_parser import ToolCallError


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
    parser.add_argument('--single', '-s',
                       action='store_true',
                       help='Run in single response mode instead of autonomous loop')
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
    def __init__(self, provider_name: str = 'deepseek_ollama', single_mode: bool = False):
        self.context_storage = ContextStorage(storage_dir="memory/context_logs")
        
        # Initialize provider first
        provider_lib = ProviderLibrary()
        self.llm = provider_lib.get_provider(provider_name)
        if not self.llm:
            available = provider_lib.list_providers()
            raise ValueError(f"Provider '{provider_name}' not found. Available providers: {available}")
            
        # Initialize prompt manager early
        self.prompt_manager = PromptManager(model_name=provider_name)
        
        if False:
            # Print the full system prompt at startup
            print("==================")
            print("\nDEBUGGING: FULL SYSTEM PROMPT")
            print("==================")
            print(self.prompt_manager.get_full_prompt())
            print("==================\n")
            print("DEBUGGING: END OF FULL SYSTEM PROMPT")
            print("==================\n")
        
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

        self.single_mode = single_mode

    def run(self):
        """Run the agent in either autonomous or single response mode."""
        parser = InlineCallParser(self.tool_manager.tools, marker="TOOL_CALL:")

        # For single mode, we don't need context or goals
        if self.single_mode:
            try:
                response = self.llm.run({
                    "messages": [
                        {"content": self.prompt_manager.get_full_prompt()}
                    ]
                })
                final_text = parser.feed(response["content"]["content"])
                print(final_text)
                print("\nEnd of response.")
                return
            except Exception as e:
                print(f"Error: {e}")
                return

        # Regular autonomous mode
        last_response = ""
        repeat_count = 0

        while self.running:
            if not self.goal:
                self.goal = self._suggest_new_goal()

            last_context = self._get_rolling_context(self.log_file, lines=50)

            step_prompt = f"""
    Current goal: {self.goal}.

    Here is some context from your previous responses (last 50 lines of logs):
    ----------------------------------------
    {last_context}
    ----------------------------------------
    End of previous context.

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

            # ------------------------------------------------------
            # STREAMING CALL to the LLM - example if your provider supports .stream()
            # ------------------------------------------------------
            try:
                stream_generator = self.llm.stream({
                    "messages": [
                        {"content": self.prompt_manager.get_full_prompt()},
                        {"content": step_prompt}
                    ]
                })
            except AttributeError:
                # Fallback if streaming isn't supported by your provider
                result = self.llm.run({
                    "messages": [
                        {"content": self.prompt_manager.get_full_prompt()},
                        {"content": step_prompt}
                    ]
                })
                # Just feed the entire text once - no true streaming
                final_text = parser.feed(result["content"]["content"])
                self.log("\n--- Your Previous Response ---")
                self.log(final_text)
                print("Sleeping for 3 seconds to avoid busy loop...")
                import time
                time.sleep(3)
                continue

            # If we do have a stream:
            final_text = ""
            for chunk in stream_generator:
                chunk_text = chunk.get("response", "")  # Or however your model yields text
                try:
                    user_text = parser.feed(chunk_text)
                    # Accumulate normal user-visible text
                    final_text += user_text

                except ToolCallError as e:
                    # The parser found a malformed tool call or tool execution error
                    error_msg = f"\n[TOOL_CALL ERROR: {e.message}]\n"
                    final_text += error_msg
                    # Optionally log it or pass it back as "Self Correction"

            # Once the stream ends, we have final_text containing 
            # everything (minus tool calls, which were handled in real-time).
            # You can now do repeated-response detection, logging, etc.

            if final_text == last_response:
                repeat_count += 1
            else:
                repeat_count = 0

            if repeat_count >= 2:
                # If LLM repeated the exact same content multiple times, you can intervene
                final_text += "\n(LLM: Please provide new content, not the same as before.)"

            self.log("\n--- Your Previous Response ---")
            self.log(final_text)

            print("Sleeping for 3 seconds to avoid busy loop...")
            import time
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
        try:
            provider_lib = ProviderLibrary()
            provider_lib.create_provider(args.new_provider)
            provider_name = f"{args.new_provider}_ollama"
            print(f"Provider '{args.new_provider}' created successfully.")
            print(f"You can now use it by specifying: --provider {provider_name}")
            sys.exit(0)
        except Exception as e:
            print(f"Error creating provider: {e}")
            sys.exit(1)
        
    # Handle prompt listing
    if args.list_prompts:
        prompt_manager = PromptManager()
        print("\nAvailable prompts:\n")
        prompt_lines = prompt_manager.list_prompts_by_folder()
        print("\n".join(prompt_lines))
        exit(0)
        
    # Handle provider listing
    if args.list_providers:
        print("\nAvailable providers:\n")
        provider_lib = ProviderLibrary()
        provider_lines = provider_lib.list_providers_by_folder()
        print("\n".join(provider_lines))
        exit(0)
        
    try:
        agent = AutonomousAgent(
            provider_name=args.provider,
            single_mode=args.single
        )
        if args.prompt:
            agent.prompt_manager.set_active_prompt(args.prompt)
        agent.run()
    except ValueError as e:
        print(f"Error: {e}")
        exit(1)
