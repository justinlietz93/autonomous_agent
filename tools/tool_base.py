# LLM_KIT/tools/tool_base.py
"""
Base classes for Anthropic Claude tool implementation.
Based on: https://docs.anthropic.com/claude/docs/tool-use
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TypedDict, List, Literal
import uuid

class ToolInput_schema(TypedDict):
    type: str
    function: Dict[str, Any]

class ToolCall(TypedDict):
    id: str
    type: str
    function: Dict[str, Any]

class ToolResult(TypedDict):
    """Standard response format for all tools.
    
    All tools must return this format to maintain consistency.
    The content field must be a string for compatibility with all tools.
    
    Example:
        {"type": "tool_result", "tool_use_id": "123", "content": "File created successfully"}
        {"type": "error", "tool_use_id": "123", "content": "Permission denied"}
    """
    type: str  # Must be either "tool_result" or "error"
    tool_use_id: str  # Unique identifier for the tool call
    content: str  # String content only for consistent handling

class Tool(ABC):
    """
    Abstract base class for tools following Anthropic Claude standards.
    See: https://docs.anthropic.com/claude/docs/tool-use
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name used in function calling format."""
        pass
        
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what the tool does."""
        pass
        
    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """Get the input schema for this tool."""
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    @abstractmethod
    def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with the given input input_schema."""
        pass

    def get_tool_definition(self) -> Dict[str, Any]:
        """Get the tool definition in Anthropic's format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": self.input_schema["properties"],
                "required": self.input_schema["required"]
            }
        }

    def format_result(self, tool_call_id: str, content: str) -> ToolResult:
        """Format a successful result in Anthropic's format."""
        # Generate UUID if no ID provided
        actual_id = tool_call_id if tool_call_id else str(uuid.uuid4())
        return {
            "type": "tool_result",
            "tool_use_id": actual_id,
            "content": content
        }

    def format_error(self, tool_call_id: str, error: str) -> ToolResult:
        """Format an error result in Anthropic's format."""
        return {
            "type": "error",
            "tool_use_id": tool_call_id,
            "content": f"Error: {error}"
        }
