from typing import Dict, Any, Optional, List
import json
import os
from datetime import datetime
from pathlib import Path

class GoalManager:
    """Manages sequences of prompts to achieve specific goals."""
    
    def __init__(self, prompt_manager):
        """Initialize the goal manager.
        
        Args:
            prompt_manager: The prompt manager instance
            
        Raises:
            ValueError: If both goal and command line prompt are specified
        """
        self.prompt_manager = prompt_manager
        
        # Validate - can't have both goal and command line prompt
        if prompt_manager.active_prompt is not None and self.current_goal is not None:
            raise ValueError("Cannot specify both --prompt and goal at the same time")
        
        self.current_goal = None
        self.current_sequence = []
        self.current_index = 0
        self.current_iterations = 0
        self.state_file = "memory/goals/goal_state.json"
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        self._load_state()

    def load_goal(self, goal_name: str) -> None:
        """Load a goal sequence."""
        goals_path = Path("prompts/goals/sequences")
        goal_file = goals_path / f"{goal_name}.json"
        
        if not goal_file.exists():
            raise ValueError(f"Goal sequence {goal_name} not found")
            
        with open(goal_file) as f:
            self.current_goal = json.load(f)
            self.current_sequence = self.current_goal["prompt_sequence"]
            # Reset state when loading new goal
            self.current_index = 0
            self.current_iterations = 0
            self._save_state()
            print(f"Loaded goal: {goal_name} with {len(self.current_sequence)} steps")

    def get_current_prompt(self) -> Optional[str]:
        """Get the current prompt name based on goal state."""
        if not self.current_sequence or self.current_index >= len(self.current_sequence):
            return None
            
        current_step = self.current_sequence[self.current_index]
        return current_step["prompt"]

    def update_progress(self, session_log: str) -> bool:
        """Update progress and check if we should move to next prompt.
        Returns True if goal is complete."""
        
        if not self.current_sequence:
            return False

        if self.current_index >= len(self.current_sequence):
            self._reset_state()
            return True

        current_step = self.current_sequence[self.current_index]
        self.current_iterations += 1
        print(f"Step {self.current_index + 1}/{len(self.current_sequence)}: "
              f"Iteration {self.current_iterations}/{current_step.get('iterations', '∞')}")

        # Check if we should move to next prompt
        should_advance = False

        # Check iteration count
        if "iterations" in current_step:
            if self.current_iterations >= current_step["iterations"]:
                should_advance = True
                print(f"Completed iterations for step {self.current_index + 1}")

        # Check condition if specified
        if "condition" in current_step:
            condition_met = self._check_condition(current_step["condition"], session_log)
            if condition_met:
                should_advance = True
                print(f"Met condition for step {self.current_index + 1}")

        if should_advance:
            self.current_index += 1
            self.current_iterations = 0
            
            # Check if goal is complete
            if self.current_index >= len(self.current_sequence):
                print("Goal sequence complete!")
                self._reset_state()
                return True
            else:
                print(f"Moving to step {self.current_index + 1}")

        self._save_state()
        return False

    def _check_condition(self, condition: str, session_log: str) -> bool:
        """Check if a condition has been met based on session log."""
        return condition.lower() in session_log.lower()

    def _reset_state(self) -> None:
        """Reset the goal state completely."""
        self.current_goal = None
        self.current_sequence = []
        self.current_index = 0
        self.current_iterations = 0
        self._save_state()

    def _save_state(self) -> None:
        """Save current goal state."""
        state = {
            "current_goal": self.current_goal,
            "current_index": self.current_index,
            "current_iterations": self.current_iterations,
            "timestamp": datetime.now().isoformat()
        }
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)

    def _load_state(self) -> None:
        """Load saved goal state if it exists."""
        if os.path.exists(self.state_file):
            with open(self.state_file) as f:
                state = json.load(f)
                self.current_goal = state.get("current_goal")
                self.current_sequence = self.current_goal["prompt_sequence"] if self.current_goal else []
                self.current_index = state.get("current_index", 0)
                self.current_iterations = state.get("current_iterations", 0) 