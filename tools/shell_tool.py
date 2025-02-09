# selfprompter/tools/shell_tool.py

import subprocess
from typing import Dict, Any, Optional, List
from .tool_base import Tool

class ShellTool(Tool):
    """
    Tool for executing shell commands safely.
    Follows Anthropic Claude tool use standards.
    
    Example usage by LLM:
        shell("ls -la")
        shell("df -h")
        shell("ps aux | grep python")
    """

    def __init__(self, allowed_commands: Optional[List[str]] = None):
        """
        Initialize with optional allowed commands whitelist.
        
        Args:
            allowed_commands: List of allowed shell commands. If None, all commands are allowed
                            (use with caution in production)
        """
        super().__init__()  # Add base class initialization
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
                    "description": "The shell command to execute. For commands that would use a pager, append '| cat'"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Command timeout in seconds (1-300)",
                    "minimum": 1,
                    "maximum": 300,
                    "default": 60
                },
                "working_dir": {
                    "type": "string",
                    "description": "Working directory for command execution. Defaults to current directory"
                },
                "background": {
                    "type": "boolean",
                    "description": "Run command in background (for long-running operations)",
                    "default": False
                }
            },
            "required": ["command"]
        }

    def _is_command_allowed(self, command: str) -> bool:
        """
        Check if command is in allowed list.
        
        Args:
            command: The shell command to validate
            
        Returns:
            bool: True if command is allowed, False otherwise
        """
        if not self.allowed_commands:
            return True
        return any(command.startswith(cmd) for cmd in self.allowed_commands)

    def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a shell command safely with proper error handling.
        
        Args:
            input: Dictionary containing:
                command: The shell command to execute
                timeout: Command timeout in seconds (default: 60)
                working_dir: Working directory for execution
                background: Run in background (default: False)
            
        Returns:
            Dictionary containing:
                type: "tool_response"
                content: Command output or error message
                success: Boolean indicating if command succeeded
                exit_code: Command exit code (if available)
        """
        try:
            command = input.get("command")
            if not command:
                return {
                    "type": "tool_response",
                    "content": "Error: Command is required",
                    "success": False
                }

            if not self._is_command_allowed(command):
                return {
                    "type": "tool_response",
                    "content": f"Error: Command '{command}' is not in the allowed list",
                    "success": False
                }

            timeout = min(max(1, input.get("timeout", 60)), 300)
            working_dir = input.get("working_dir")
            background = input.get("background", False)

            # Handle background processes differently
            if background:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=working_dir
                )
                return {
                    "type": "tool_response",
                    "content": f"Command started in background with PID {process.pid}",
                    "success": True,
                    "pid": process.pid
                }

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=working_dir
            )

            response = {
                "type": "tool_response",
                "success": result.returncode == 0,
                "exit_code": result.returncode
            }

            if result.returncode != 0:
                error_msg = result.stderr.strip() or f"Command failed with exit code {result.returncode}"
                response["content"] = f"Error: {error_msg}"
            else:
                response["content"] = result.stdout.strip() or "Command executed successfully (no output)"

            return response

        except subprocess.TimeoutExpired:
            return {
                "type": "tool_response",
                "content": f"Error: Command timed out after {timeout} seconds",
                "success": False
            }
        except Exception as e:
            return {
                "type": "tool_response",
                "content": f"Error: {str(e)}",
                "success": False
            }