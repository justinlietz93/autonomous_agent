# main_autonomous.py
# Entry point to run the system indefinitely and pursue goals automatically.

import os
import time
from datetime import datetime
from memory.context_manager import ContextStorage
from tools.tool_manager import ToolManager
from providers.deepseek_ollama_provider import OllamaDeepSeekProvider
from prompts.system_prompts import SELECTED_PROMPT
from typing import Dict, Any
import random

class AutonomousAgent:
    """
    An autonomous agent that runs indefinitely, sets & pursues goals, 
    and spawns new goals when each is achieved.
    """

    def __init__(self):
        self.context_storage = ContextStorage(storage_dir="memory/context_logs")
        self.tool_manager = ToolManager(register_defaults=True)
        self.goal = "Initialize a simple demonstration goal"
        self.session_id = "autonomous_session_01"  # arbitrary
        self.running = True

        # Create a unique filename to store logs for this session
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_file = os.path.join("memory", "context_logs", f"context_{timestamp_str}_{self.session_id}.txt")

    def run(self):
        while self.running:
            if not self.goal:
                self.goal = self._suggest_new_goal()

            # 1) Retrieve the last ~20 lines from our session log
            last_context = self._get_rolling_context(self.log_file, lines=20)

            # 2) Build the next step prompt with the rolling context
            step_prompt = f"""
You are an autonomous agent. 
Current goal: {self.goal}.

Here is the recent context (last 20 lines of logs):
----------------------------------------
{last_context}
----------------------------------------

Plan your next step. You can call any tool if needed. 
If you've achieved your goal, test your system to ensure it's working as expected.
"""

            # 3) Log out the prompt so we can see it (and it goes into the log file)
            self.log("=== Next Step Prompt ===")
            self.log(step_prompt)

            # 4) Send the prompt to our local Ollama-based LLM
            provider = OllamaDeepSeekProvider()
            result = provider.run({
                "messages": [
                    {"content": SELECTED_PROMPT}, 
                    {"content": step_prompt}
                ]
            })

            # 5) The provider’s streaming response is already printed in real-time 
            #    because of how OllamaDeepSeekProvider is coded, but let's also 
            #    gather the final chunk and log it.
            response_content = result["content"]["content"]
            self.log("\n--- Agent Response ---")
            self.log(response_content)

            # 6) Check if the agent claims "Goal Achieved"
            if "Goal Achieved" in response_content or "[GOAL_ACHIEVED]" in response_content:
                self.log("Goal has been marked achieved. Generating a new goal...\n")
                self.goal = self._suggest_new_goal()
                continue

            # 7) Sleep or wait to avoid busy loop
            print("Sleeping for 5 seconds to avoid busy loop...")
            time.sleep(5)

    def _suggest_new_goal(self) -> str:
        suggestions = [
            "Improve internal memory documentation",
            "Find new ways to self-optimize and reduce token usage",
            "Investigate new data sources for knowledge updates",
            "Improve performance in tool usage"
            "Write low level AMD GPU driver packages to optimize GPU utilization for LLMs"
        ]
        return random.choice(suggestions)

    def log(self, message: str):
        """
        Logs a message both to console (stdout) and appends to the session log file.
        """
        print(message)  # Normal terminal output
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(message + "\n")
        except Exception as e:
            print(f"[WARNING] Could not write to log file: {e}")

    def _get_rolling_context(self, filepath: str, lines: int = 100) -> str:
        """
        Reads the last `lines` lines from the given log file.
        Returns them as a string. If file doesn’t exist, returns empty string.
        """
        if not os.path.exists(filepath):
            return ""  # No file yet, no context

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
            # Grab the last `lines` lines
            snippet = all_lines[-lines:] if len(all_lines) > lines else all_lines
            return "".join(snippet).strip()
        except Exception as e:
            return f"[ERROR reading log: {e}]"


if __name__ == "__main__":
    agent = AutonomousAgent()
    agent.run()
