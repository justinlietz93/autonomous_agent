# LLM_KIT/tools/shell_tool.py

import subprocess
from typing import Dict, Any, Optional, List
from .tool_base import Tool
from .types import ToolResult

class ShellTool(Tool):
    """
    Tool for executing shell commands safely.
    Follows Anthropic Claude tool use standards.
    """

    def __init__(self, allowed_commands: Optional[List[str]] = None):
        """
        Initialize with optional allowed commands whitelist.
        
        Args:
            allowed_commands: List of allowed shell commands
        """
        self.allowed_commands = allowed_commands or []

    @property
    def name(self) -> str:
        return "shell"

    @property
    def description(self) -> str:
        return (
            "Executes shell commands in a controlled environment. Commands are validated "
            "against a whitelist if provided. Returns command output or error messages."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Command timeout in seconds",
                    "minimum": 1,
                    "maximum": 300,
                    "default": 60
                },
                "working_dir": {
                    "type": "string",
                    "description": "Working directory for command execution"
                }
            },
            "required": ["command"]
        }

    def _is_command_allowed(self, command: str) -> bool:
        """Check if command is in allowed list."""
        if not self.allowed_commands:
            return True
        return any(command.startswith(cmd) for cmd in self.allowed_commands)

    def run(self, input: Dict[str, Any]) -> ToolResult:
        """
        Execute a shell command.
        
        Args:
            input: Dictionary containing:
                command: The shell command to execute
                timeout: Command timeout in seconds (default: 60)
                working_dir: Working directory for execution
            
        Returns:
            Dictionary containing command output or error message
        """
        try:
            command = input.get("command")
            if not command:
                return self.format_error("", "Command is required")

            if not self._is_command_allowed(command):
                return self.format_error("", f"Command '{command}' is not in the allowed list")

            timeout = min(max(1, input.get("timeout", 60)), 300)
            working_dir = input.get("working_dir")

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=working_dir
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or f"Command failed with exit code {result.returncode}"
                return self.format_error("", error_msg)

            output = result.stdout.strip() or "Command executed successfully (no output)"
            return self.format_result("", output)

        except subprocess.TimeoutExpired:
            return self.format_error("", f"Command timed out after {timeout} seconds")
        except Exception as e:
            return self.format_error("", str(e))
