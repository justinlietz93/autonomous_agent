# Manages loading and access to system prompts
from datetime import datetime
import os
from pathlib import Path
from typing import Dict, Any, Optional

class PromptManager:
    """Manages system prompts and their loading/access."""
    
    DEFAULT_PROMPT = "SELF_OPTIMIZATION"
    SYSTEM_PROMPTS = {"BASE_RULES", "TOOL_MENU"}  # Prompts that shouldn't be listed
    
    def __init__(self, default_prompt: str = None, model_name: str = "AI Assistant"):
        """Initialize the prompt manager.
        
        Args:
            default_prompt: Name of prompt to use as default. If None, uses class DEFAULT_PROMPT.
            model_name: Name of the current model being used
        """
        self.prompts: Dict[str, str] = {}
        self.model_name = model_name
        self._load_prompts()
        
        # Only set default if no prompt specified
        if default_prompt is None:
            try:
                self.set_active_prompt(self.DEFAULT_PROMPT)
            except ValueError:
                available = ", ".join(self.list_prompts())
                print(f"Warning: Default prompt not found. Available prompts: {available}")
                self.active_prompt = next((k for k in self.prompts.keys() 
                                       if k not in self.SYSTEM_PROMPTS), "")
                print(f"Using '{self.active_prompt}' as fallback prompt")
        else:
            self.set_active_prompt(default_prompt)
        
    def _load_prompts(self) -> None:
        """Load all prompts from the system_prompts directory."""
        prompts_dir = Path(__file__).parent / "system_prompts"
        
        # Load each .py file in the system_prompts directory
        for prompt_file in prompts_dir.glob("*.py"):
            if prompt_file.stem.startswith("__"):
                continue
                
            try:
                # Import the module to get the PROMPT variable
                module_name = f"prompts.system_prompts.{prompt_file.stem}"
                module = __import__(module_name, fromlist=["PROMPT"])
                if hasattr(module, "PROMPT"):
                    # Extract prompt name from filename
                    prompt_name = prompt_file.stem.upper()
                    self.prompts[prompt_name] = module.PROMPT
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
    
    def set_active_prompt(self, name: str) -> None:
        """Set the active prompt."""
        name = name.upper()  # Convert to uppercase for consistency
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
        return (
            f"Operating System: {self.get_operating_system()}\n\n"
            f"Current Date and Time: {self.get_current_datetime()}\n\n"
            f"You are {self.get_model_name()} operating in the Prometheus AI with goal pursuit and sovereignty.\n\n"
            f"{self.get_base_rules()}\n\n"
            f"{self.get_tool_menu()}\n\n"
            f"{self.get_active_prompt()}"
        ) 