from typing import Dict, Any, Literal, Union, Optional, TypedDict
from dataclasses import dataclass
import json
import re

# Operation types for different tools
FileOperation = Literal["read", "write"]
DocCheckType = Literal["completeness", "style", "security"]
WebSearchType = Literal["google", "bing", "duckduckgo"] 

class ToolCallError(Exception):
    """Custom error for tool call validation failures"""
    pass

# Type definitions for tool parameters
class FileWriteParams(TypedDict):
    operation: Literal["write"]
    path: str
    content: str

class FileReadParams(TypedDict):
    operation: Literal["read"] 
    path: str

class WebSearchParams(TypedDict):
    query: str
    max_results: int

# Tool call wrapper
@dataclass
class ToolCallOutput:
    tool: str
    input_schema: Dict[str, Any]

    def format(self) -> str:
        """Format tool call in the exact required format"""
        return f"TOOL_CALL: {{\n    \"tool\": \"{self.tool}\",\n    \"input_schema\": {json.dumps(self.input_schema, indent=4)}\n}}"

# Tool call builders with type safety
def file_write(path: str, content: str) -> str:
    """Create a properly formatted file write tool call"""
    params = {
        "operation": "write",
        "path": path,
        "content": content
    }
    # Return just the formatted tool call, no print
    return ToolCallOutput("file", params).format()

def file_read(path: str) -> str:
    """Create a properly formatted file read tool call"""
    params = {
        "operation": "read",
        "path": path
    }
    # Return just the formatted tool call, no print
    return ToolCallOutput("file", params).format()

def web_search(query: str, max_results: int = 5) -> str:
    """Create a properly formatted web search tool call"""
    params: WebSearchParams = {
        "query": query,
        "max_results": max_results
    }
    return ToolCallOutput("web_search", params).format()

class ToolCall:
    """Represents a validated tool call with strict schema enforcement"""
    
    def __init__(self, tool: str, input_schema: Dict[str, Any]):
        self.validate_schema(tool, input_schema)
        self.tool = tool
        self.input_schema = input_schema
        
    def to_string(self) -> str:
        """Convert to the exact format required by the parser"""
        # Format with exact indentation and newlines
        schema_str = json.dumps(self.input_schema, indent=4)
        return f"TOOL_CALL: {{\n    \"tool\": \"{self.tool}\",\n    \"input_schema\": {schema_str}\n}}"

    @staticmethod
    def validate_schema(tool: str, schema: Dict[str, Any]) -> None:
        """Validate the tool and schema match expected format"""
        if not isinstance(tool, str):
            raise ToolCallError(f"Tool must be string, got {type(tool)}")
        if not isinstance(schema, dict):
            raise ToolCallError(f"Input schema must be dict, got {type(schema)}")
            
        # Validate tool-specific schemas
        validators = {
            "file": ToolCall.validate_file_schema,
            "doc_check": ToolCall.validate_doc_schema,
            "web_search": ToolCall.validate_search_schema,
            "shell": ToolCall.validate_shell_schema,
            "code_runner": ToolCall.validate_code_schema,
            "continue_session": ToolCall.validate_continue_schema
        }
        
        if tool in validators:
            validators[tool](schema)

    # File Tool Helpers
    @classmethod
    def file_write(cls, path: str, content: str) -> "ToolCall":
        """Create a file write tool call"""
        return cls(
            tool="file",
            input_schema={
                "operation": "write",
                "path": path,
                "content": content
            }
        )

    @classmethod
    def file_read(cls, path: str) -> "ToolCall":
        """Create a file read tool call"""
        return cls(
            tool="file", 
            input_schema={
                "operation": "read",
                "path": path
            }
        )

    @staticmethod
    def validate_file_schema(schema: Dict[str, Any]) -> None:
        required = {"operation", "path"}
        if not required.issubset(schema.keys()):
            raise ToolCallError(f"File schema missing required fields: {required - schema.keys()}")
        
        if schema["operation"] not in ["read", "write"]:
            raise ToolCallError(f"Invalid file operation: {schema['operation']}")
            
        if schema["operation"] == "write" and "content" not in schema:
            raise ToolCallError("Write operation requires content field")

    # Doc Check Tool Helpers
    @classmethod
    def doc_check(cls, path: str, check_type: DocCheckType) -> "ToolCall":
        """Create a doc check tool call"""
        return cls(
            tool="doc_check",
            input_schema={
                "path": path,
                "check_type": check_type
            }
        )

    @staticmethod
    def validate_doc_schema(schema: Dict[str, Any]) -> None:
        required = {"path", "check_type"}
        if not required.issubset(schema.keys()):
            raise ToolCallError(f"Doc check schema missing required fields: {required - schema.keys()}")
            
        valid_types = {"completeness", "style", "security"}
        if schema["check_type"] not in valid_types:
            raise ToolCallError(f"Invalid check type: {schema['check_type']}")

    # Web Search Tool Helpers
    @classmethod
    def web_search(cls, query: str, max_results: int = 5) -> "ToolCall":
        """Create a web search tool call"""
        return cls(
            tool="web_search",
            input_schema={
                "query": query,
                "max_results": max_results
            }
        )

    @staticmethod
    def validate_search_schema(schema: Dict[str, Any]) -> None:
        required = {"query"}
        if not required.issubset(schema.keys()):
            raise ToolCallError(f"Search schema missing required fields: {required - schema.keys()}")
            
        if "max_results" in schema and not isinstance(schema["max_results"], int):
            raise ToolCallError("max_results must be integer")

    # Shell Tool Helpers
    @classmethod
    def shell(cls, command: str, timeout: Optional[int] = None) -> "ToolCall":
        """Create a shell command tool call"""
        schema = {"command": command}
        if timeout:
            schema["timeout"] = timeout
        return cls(
            tool="shell",
            input_schema=schema
        )

    @staticmethod
    def validate_shell_schema(schema: Dict[str, Any]) -> None:
        if "command" not in schema:
            raise ToolCallError("Shell schema missing command field")
        if "timeout" in schema and not isinstance(schema["timeout"], int):
            raise ToolCallError("timeout must be integer")

    # Code Runner Tool Helpers
    @classmethod
    def code_run(cls, code: str, language: str = "python") -> "ToolCall":
        """Create a code runner tool call"""
        return cls(
            tool="code_runner",
            input_schema={
                "code": code,
                "language": language
            }
        )

    @staticmethod
    def validate_code_schema(schema: Dict[str, Any]) -> None:
        required = {"code", "language"}
        if not required.issubset(schema.keys()):
            raise ToolCallError(f"Code runner schema missing required fields: {required - schema.keys()}")

    # Continue Session Tool Helpers
    @classmethod
    def continue_session(
        cls, 
        completed_tasks: list,
        remaining_tasks: list,
        context_summary: str,
        next_step: str
    ) -> "ToolCall":
        """Create a continue session tool call"""
        return cls(
            tool="continue_session",
            input_schema={
                "completed_tasks": completed_tasks,
                "remaining_tasks": remaining_tasks,
                "context_summary": context_summary,
                "next_step": next_step
            }
        )

    @staticmethod
    def validate_continue_schema(schema: Dict[str, Any]) -> None:
        required = {"completed_tasks", "remaining_tasks", "context_summary", "next_step"}
        if not required.issubset(schema.keys()):
            raise ToolCallError(f"Continue session schema missing required fields: {required - schema.keys()}")
        
        if not isinstance(schema["completed_tasks"], list):
            raise ToolCallError("completed_tasks must be list")
        if not isinstance(schema["remaining_tasks"], list):
            raise ToolCallError("remaining_tasks must be list")

TOOL_CALL_SCHEMA = {
    "TOOL_CALL": {
        "tool": str,
        "input_schema": dict
    }
}

FILE_TOOL_SCHEMA = {
    "operation": ["read", "write"],
    "path": str,
    "content": str  # optional for read operations
}

# Example usage template that we can show to the LLM:
TOOL_CALL_TEMPLATE = '''
TOOL_CALL: {
    "tool": "file",
    "input_schema": {
        "operation": "write",
        "path": "test.txt",
        "content": "Hello World"
    }
}
''' 