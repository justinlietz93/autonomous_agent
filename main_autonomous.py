#!/usr/bin/env python3

import os
import re
import json
import random
import time
import argparse
import sys
from datetime import datetime
from typing import Dict, Any
import string
from providers.utils.safe_chunker import SafeChunker
from providers.utils.stream_smoother import StreamSmoother
from tools.parse_formatter import InlineCallParser
from tools.tool_parser import ToolCallError, RealTimeToolParser
from memory.context_manager import ContextStorage
from tools.tool_manager import ToolManager
from providers.provider_library import ProviderLibrary
from prompts.prompt_manager import PromptManager
from prompts.goals.goal_manager import GoalManager


def parse_args():
    parser = argparse.ArgumentParser(description='Run autonomous agent with specified LLM provider')
    parser.add_argument('--provider', '-p', 
                       default='claude-3-5-sonnet-20241022_api',
                       help='Name of the LLM provider to use (default: claude-3-5-sonnet-20241022_api)')
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
    parser.add_argument('--goal', type=str,
                       help="Name of the goal sequence to run (e.g. memory_development)")
    return parser.parse_args()


class AutonomousAgent:
    def __init__(self, provider_name: str = 'claude-3-5-sonnet-20241022_api', single_mode: bool = False, goal_name: str = None):
        # 1) Initialize context storage
        self.context_storage = ContextStorage(storage_dir="memory/context_logs")

        # 2) Create tool manager first
        self.tool_manager = ToolManager(register_defaults=True)

        # 3) Load the chosen LLM provider
        provider_lib = ProviderLibrary()
        self.llm = provider_lib.get_provider(provider_name, tool_manager=self.tool_manager)
        if not self.llm:
            available = provider_lib.list_providers()
            raise ValueError(f"Provider '{provider_name}' not found. Available providers: {available}")
        print(f"Loaded provider: {provider_name}")

        # 4) Initialize a PromptManager
        self.prompt_manager = PromptManager(model_name=provider_name)

        # 5) Create goal manager and load goal if specified
        ### THIS MIGHT BREAK SOMETHING, VERIFY ###
        self.goal_manager = GoalManager(self.prompt_manager)
        if goal_name:
            self.goal_manager.load_goal(goal_name)
            # Now update prompt_manager with the goal's first prompt
            first_prompt = self.goal_manager.get_current_prompt()
            if first_prompt:
                self.prompt_manager.set_active_prompt(first_prompt)
        ### THIS MIGHT BREAK SOMETHING, VERIFY ###

        # Register the provider with the tool manager
        self.tool_manager.llm_provider = self.llm
        if not self.tool_manager.tools:
            print("WARNING: No tools were registered!")

        self.goal = "FOLLOW ALL INSTRUCTIONS EXPLICITLY. FORMAT TOOL CALLS CORRECTLY."
        self.single_mode = single_mode
        self.running = True

        # 5) Session log file
        random_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        prompt_name = self.prompt_manager.active_prompt.lower()
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.session_id = f"{prompt_name}_{random_chars}"
        self.log_file = os.path.join("memory", "context_logs", f"context_{timestamp_str}_{self.session_id}.txt")

        # print("Registered tools:", list(self.tool_manager.tools.keys()))

    def run(self):
        """
        Run in either single response mode or multi-step autonomous mode.
        """
        # First create the inline parser to convert function calls to TOOL_CALL format
        inline_parser = InlineCallParser(self.tool_manager.tools)
        
        # Then create the tool parser to execute the TOOL_CALL formatted calls
        tool_parser = RealTimeToolParser(tools=self.tool_manager.tools)

        # Single mode: Just do one call with your "active prompt"
        if self.single_mode:
            try:
                response = self.llm.run({
                    "messages": [
                        {"content": self.prompt_manager.get_full_prompt()}
                    ]
                })
                final_text = inline_parser.feed(response["content"]["content"])
                print(final_text)
                print("\nEnd of single response.")
                return
            except Exception as e:
                print(f"Error: {e}")
                return

        # Otherwise do an indefinite autonomous loop
        last_response = ""
        repeat_count = 0

        while self.running:
            # If there's no self.goal set
            if not self.goal:
                self.goal = "Manually write a new prompt or do something else."

            # Grab rolling context from log
            last_context = self._get_rolling_context(self.log_file, lines=50)

            # Build a step prompt
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

            # 1) Attempt a streaming call
            final_text = ""
            try:
                stream_generator = self.llm.stream({
                    "messages": [
                        {"content": self.prompt_manager.get_full_prompt()},
                        {"content": step_prompt}
                    ]
                })
            except AttributeError:
                # fallback if streaming not supported
                result = self.llm.run({
                    "messages": [
                        {"content": self.prompt_manager.get_full_prompt()},
                        {"content": step_prompt}
                    ]
                })
                final_text = inline_parser.feed(result["content"]["content"])
                self.log("\n--- Your Previous Response ---")
                self.log(final_text)
                print("Sleeping for 3 seconds to avoid busy loop...")
                time.sleep(3)
                continue

            # 2) We do typed-lag loop
            for chunk in stream_generator:
                chunk_text = chunk.get("response", "")
                try:
                    # First convert function calls to TOOL_CALL format
                    formatted_text = inline_parser.feed(chunk_text)
                    # print("\nDEBUG: After inline parser:", formatted_text)
                    
                    # Then execute any tool calls and get final text
                    user_text = tool_parser.feed(formatted_text)
                    # print("DEBUG: After tool parser:", user_text)
                    
                    final_text += user_text
                    sys.stdout.write(user_text)
                    sys.stdout.flush()

                except ToolCallError as e:
                    error_msg = f"\n[TOOL_CALL ERROR: {e.message}]\n"
                    final_text += error_msg
                    sys.stdout.write(error_msg)
                    sys.stdout.flush()

            # 3) After streaming ends, we have final_text
            if final_text == last_response:
                repeat_count += 1
            else:
                repeat_count = 0

            if repeat_count >= 2:
                # If repeated same content multiple times, append a note
                final_text += "\n(LLM: Please provide new content, not the same as before.)"

            self.log("\n--- Your Previous Response ---")
            self.log(final_text)

            # Sleep a bit to avoid a tight loop
            print("Sleeping for 3 seconds to avoid busy loop...")
            time.sleep(3)
            last_response = final_text

            ### THIS MIGHT BREAK SOMETHING, VERIFY ###
            # Check goal progress
            if self.goal_manager.current_goal:
                goal_complete = self.goal_manager.update_progress(final_text)
                if goal_complete:
                    print("Goal sequence complete!")
                    self.running = False
                else:
                    # Update prompt for next iteration
                    next_prompt = self.goal_manager.get_current_prompt()
                    if next_prompt:
                        self.prompt_manager.set_active_prompt(next_prompt)

            ### THIS MIGHT BREAK SOMETHING, VERIFY ###

    def log(self, message: str):
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(message + "\n")
        except Exception as e:
            print(f"[WARNING] Could not write to log file: {e}")
            import traceback
            print("Full error:")
            print(traceback.format_exc())

    def _get_rolling_context(self, filepath: str, lines: int = 20) -> str:
        if not os.path.exists(filepath):
            return ""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
                # print(f"DEBUG: Read {len(all_lines)} lines from log file")
                snippet = all_lines[-lines:] if len(all_lines) > lines else all_lines
                return "".join(snippet).strip()
        except Exception as e:
            return f"[ERROR reading log: {e}]"


if __name__ == "__main__":
    args = parse_args()

    # 1) Possibly create new provider
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

    # 2) Possibly list prompts
    if args.list_prompts:
        prompt_manager = PromptManager()
        print("\nAvailable prompts:\n")
        prompt_lines = prompt_manager.list_prompts_by_folder()
        print("\n".join(prompt_lines))
        sys.exit(0)

    # 3) Possibly list providers
    if args.list_providers:
        provider_lib = ProviderLibrary()
        provider_lines = provider_lib.list_providers_by_folder()
        print("\nAvailable providers:\n")
        print("\n".join(provider_lines))
        sys.exit(0)

    # 4) Launch agent
    try:
        agent = AutonomousAgent(
            provider_name=args.provider, 
            single_mode=args.single,
            goal_name=args.goal  # Pass goal name to agent
        )
        
        # Only set prompt if no goal is specified
        if args.prompt and not args.goal:
            agent.prompt_manager.set_active_prompt(args.prompt)
        
        agent.run()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
