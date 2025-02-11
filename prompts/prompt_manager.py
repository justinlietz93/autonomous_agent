# Manages loading and access to system prompts
from datetime import datetime
import os
from pathlib import Path
from typing import Dict, Any, Optional

class PromptManager:
    """Manages system prompts and their loading/access."""
    
    DEFAULT_PROMPT = "SELF_OPTIMIZATION"
    SYSTEM_PROMPTS = {"BASE_RULES", "TOOL_MENU"}  # Prompts that shouldn't be listed
    BENCHMARK_PROMPTS = {"*_BENCHMARK"}  # Add your benchmark prompts here
    
    def __init__(self, default_prompt: str = None, model_name: str = "AI Assistant", goal_prompt: str = None):
        """Initialize the prompt manager."""
        self.prompts: Dict[str, str] = {}
        self.model_name = model_name
        self.active_prompt = None  # Initialize this first
        self._load_prompts()
        
        # Only validate and set prompt if one is provided
        if default_prompt is not None or goal_prompt is not None:
            # Validate inputs first - must have exactly one prompt source
            if default_prompt is not None and goal_prompt is not None:
                raise ValueError("Cannot specify both --prompt and goal at the same time")
            if default_prompt is None and goal_prompt is None:
                raise ValueError("Must specify either --prompt or set a goal")

            # Now we know we have exactly one prompt, use it
            self.set_active_prompt(default_prompt if default_prompt is not None else goal_prompt)
        
    def _load_prompts(self) -> None:
        """Load all prompts recursively from the system_prompts directory and subdirectories."""
        prompts_dir = Path(__file__).parent / "system_prompts"
        self.prompt_folders = {}  # Reset or initialize (folder -> { prompt_name: prompt_text })
        self.prompts = {}         # If you still want direct name->prompt_text (optional)

        for prompt_file in prompts_dir.rglob("*.py"):
            if prompt_file.stem.startswith("__"):
                continue

            try:
                # The folder immediately under system_prompts
                parent_folder = prompt_file.parent.name.upper()  # e.g. "SYSTEM_PROMPTS" or "BENCHMARKS"

                # Build an import path for the module
                rel_path = prompt_file.relative_to(prompts_dir)
                module_path = f"prompts.system_prompts.{str(rel_path.with_suffix('')).replace(os.sep, '.')}"

                module = __import__(module_path, fromlist=["PROMPT"])
                if hasattr(module, "PROMPT"):
                    prompt_name = prompt_file.stem.upper()
                    prompt_text = module.PROMPT

                    # Ensure we have a sub-dict for this folder
                    if parent_folder not in self.prompt_folders:
                        self.prompt_folders[parent_folder] = {}

                    # Store the prompt text by [folder][prompt]
                    self.prompt_folders[parent_folder][prompt_name] = prompt_text

                    # Optional: also store it in self.prompts with just the prompt name
                    # If you worry about collisions across folders, handle that carefully
                    self.prompts[prompt_name] = prompt_text

            except Exception as e:
                print(f"Warning: Failed to load prompt from {prompt_file}: {e}")


    def get_operating_system(self) -> str:
        """Get the operating system."""
        return os.name
    

    def get_current_datetime(self) -> str:
        """Get the current datetime."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def get_prompt(self, name: str) -> Optional[str]:
        """Get a specific prompt by name."""
        return self.prompts.get(name)
    
    def list_prompts(self) -> list[str]:
        """List all available prompts (excluding system prompts)."""
        return sorted([p for p in self.prompts.keys() 
                      if p not in self.SYSTEM_PROMPTS])
    
    def list_prompts_by_folder(self) -> list[str]:
        """
        Return a list of lines describing available prompts grouped by their parent folder.
        """
        lines = []

        for folder_name in sorted(self.prompt_folders.keys()):
            lines.append(folder_name)
            lines.append("-" * 40)
            prompt_names = sorted(self.prompt_folders[folder_name].keys())
            for p_name in prompt_names:
                lines.append(f"  - {p_name}")
            lines.append("")  # blank line after each folder block

        return lines



    def set_active_prompt(self, name: str) -> None:
        """Set the active prompt by name."""
        if name not in self.prompts:
            available = ", ".join(self.list_prompts())
            raise ValueError(f"Prompt '{name}' not found. Available prompts: {available}")
        self.active_prompt = name

    
    def get_active_prompt(self) -> str:
        """Get the currently active prompt."""
        return self.prompts[self.active_prompt]
    
    def get_base_rules(self) -> str:
        """Get the base rules that apply to all prompts."""
        return self.get_prompt("BASE_RULES") or ""
    
    def get_tool_menu(self) -> str:
        """Get the tool menu."""
        return self.get_prompt("TOOL_MENU") or ""
    
    def get_model_name(self) -> str:
        """Get the current model name."""
        return self.model_name
    
    def get_full_prompt(self) -> str:
        """Get the complete prompt with menu, rules and active prompt."""
        # Check if current prompt is a benchmark prompt
        if self.active_prompt in self.BENCHMARK_PROMPTS:
            return (
                f"Operating System: {self.get_operating_system()}\n\n"
                f"Current Date and Time: {self.get_current_datetime()}\n\n"
                f"{self.get_active_prompt()}"
            )
        
        # Regular full prompt for non-benchmark prompts
        return (
            f"Operating System: {self.get_operating_system()}\n\n"
            f"Current Date and Time: {self.get_current_datetime()}\n\n"
            f"You are {self.get_model_name()} operating in the Prometheus AI with goal pursuit and full sovereignty.\n\n"
            f"{self.get_base_rules()}\n\n"
            f"{self.get_tool_menu()}\n\n"
            f"{self.get_active_prompt()}"
            "FOLLOW TOOL INSTRUCTIONS EXACTLY."
        ) 