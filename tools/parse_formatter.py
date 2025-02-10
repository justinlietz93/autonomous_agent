#########################################################

# ATTENTION: THERE MAY BE ISSUES WITH THIS FILE.
# TOOL CALL FORMATS ARE NOT ALWAYS CORRECTLY HANDED TO THE tool_parser.py SCRIPT.
# PLEASE REVIEW THE TOOL SIGNATURES, AND MAKE SURE THIS LOGIC MATCHES THE REQUIREMENTS.

# IF YOU FIND ISSUES DOCUMENT THEM IN docs/tool_pipeline_issues.md

#########################################################   




import re
import json
from typing import Any, Dict, List, Union, Optional
from dataclasses import dataclass

from tools.tool_parser import RealTimeToolParser, ToolCallError

@dataclass
class ToolSchema:
    """Schema definition for a tool's input and output."""
    input_schema: Dict[str, type]
    required_fields: List[str]

class ValidationError(Exception):
    """Raised when tool input validation fails."""
    def __init__(self, message: str, details: Optional[Dict] = None):
        self.details = details or {}
        super().__init__(message)

class InlineCallParser:
    """
    A unified parser that:
      1) Finds inline calls like shell("df -h")
      2) Converts them into structured JSON with 'TOOL_CALL: {...}'
      3) Feeds the new text (with 'TOOL_CALL: {...}') into a RealTimeToolParser
         to execute the tool in real time.

    Example usage in your AutonomousAgent:
        self.parser = InlineCallParser(self.tools_dict)
    Then:
        user_text = self.parser.feed(chunk)
    """

    # A simple mapping from inline function names to actual tool names
    # (like in your test_tool_call.py)
    TOOL_NAME_MAP = {
        "print": "code_runner",
        "code_runner": "code_runner",
        "shell": "shell",
        "documentation_check": "documentation_check",
        "file_read": "file",
        "file_write": "file",
        "file_delete": "file",
        "list_dir": "file",
        "web_search": "web_search",
        "web_browser": "web_browser",
        "http_request": "http_request",
        "package_manager": "package_manager",
        "write_memory": "memory",
        "read_memory": "memory",
        "list_memory": "memory"
    }

    # Tool schemas define expected types and required fields
    TOOL_SCHEMAS = {
        "code_runner": ToolSchema(
            input_schema={
                "files": list,
                "main_file": str,
                "language": str
            },
            required_fields=["files", "main_file"]
        ),
        "file": ToolSchema(
            input_schema={
                "operation": str,  # can be "read", "write", "delete", "list_dir"
                "path": str,
                "content": str
            },
            required_fields=["operation", "path"]
        ),
        "shell": ToolSchema(
            input_schema={
                "command": str
            },
            required_fields=["command"]
        ),
        "web_search": ToolSchema(
            input_schema={
                "query": str,
                "max_results": int
            },
            required_fields=["query"]
        ),
        "web_browser": ToolSchema(
            input_schema={
                "url": str,
                "extract_type": str
            },
            required_fields=["url"]
        ),
        "documentation_check": ToolSchema(
            input_schema={
                "path": str
            },
            required_fields=["path"]
        ),
        "http_request": ToolSchema(
            input_schema={
                "method": str,
                "url": str
            },
            required_fields=["method", "url"]
        ),
        "package_manager": ToolSchema(
            input_schema={
                "action": str,
                "package": str
            },
            required_fields=["action"]
        ),
        "memory": ToolSchema(
            input_schema={
                "operation": str,
                "key": str,
                "value": str
            },
            required_fields=["operation", "key"]
        ),
    }

    def __init__(self, tool_functions: Dict[str, Any], marker: str = "TOOL_CALL:"):
        """
        Args:
            tool_functions: a dict {tool_name: callable(**kwargs) -> str}
                Typically, this is the same dictionary you'd pass to RealTimeToolParser.
                E.g. { "shell": shell_function, "file": file_function, ... }
            marker: The marker that indicates a JSON tool call block. Default "TOOL_CALL:"
        """
        # We'll create a RealTimeToolParser to handle actual JSON
        self.rtp = RealTimeToolParser(tools=tool_functions, marker=marker)
        # The partial text buffer for finding inline calls
        self.buffer = ""
        # The marker for structured calls
        self.marker = marker

    def validate_input(self, tool_name: str, input_data: Dict[str, Any]) -> None:
        """Validate tool input against its schema."""
        if tool_name not in self.TOOL_SCHEMAS:
            raise ValidationError(f"Unknown tool: {tool_name}")
            
        schema = self.TOOL_SCHEMAS[tool_name]
        
        # Check required fields
        for field in schema.required_fields:
            if field not in input_data:
                raise ValidationError(
                    f"Missing required field '{field}' for tool '{tool_name}'",
                    {"field": field}
                )
        
        # Validate types
        for field, value in input_data.items():
            if field in schema.input_schema:
                expected_type = schema.input_schema[field]
                if not isinstance(value, expected_type):
                    raise ValidationError(
                        f"Invalid type for field '{field}' in tool '{tool_name}'. "
                        f"Expected {expected_type.__name__}, got {type(value).__name__}",
                        {"field": field, "expected": expected_type.__name__, "got": type(value).__name__}
                    )

    def feed(self, text_chunk: str, debug: bool = True) -> str:
        try:
            self.buffer += text_chunk
            output_text = ""

            # while True:
            #     match = re.search(r'(?:^|\s+)(\w+)\s*\(', self.buffer, re.MULTILINE)
            while True:
                match = re.search(r'\b(\w+)\s*\(', self.buffer)
                 
                if not match:
                    break

                func_name = match.group(1)
                if debug:
                    print(f"DEBUG: Found tool call: {func_name}")

                if func_name not in self.TOOL_NAME_MAP:
                    output_text += self.buffer[:match.end()]
                    self.buffer = self.buffer[match.end():]
                    continue

                start_index = match.start()
                paren_level = 1
                i = match.end()
                while i < len(self.buffer) and paren_level > 0:
                    if self.buffer[i] == '(':
                        paren_level += 1
                    elif self.buffer[i] == ')':
                        paren_level -= 1
                    i += 1

                if paren_level != 0:
                    # Incomplete call - keep buffer and break
                    break

                # Extract ONLY the arguments between the parentheses
                inline_call_str = self.buffer[start_index:i]
                arg_start = inline_call_str.find('(') + 1
                arg_str = inline_call_str[arg_start:-1]

                parsed_args = self._parse_args(arg_str)
                tool_call_json = self._format_tool_call(func_name, parsed_args)
                
                if debug:
                    print(f"DEBUG: Formatted JSON: {tool_call_json}")

                # Send to parser and get result immediately
                tool_call_str = self.marker + json.dumps(tool_call_json)
                result = self.rtp.feed(tool_call_str)

                # Replace the inline call text with the tool result, so it actually
                # shows up in final output rather than leaving the original inline call.
                parsed_part = self.buffer[:start_index]
                remaining_part = self.buffer[i:]
                output_text += parsed_part + result
                self.buffer = remaining_part

            # Handle any remaining text
            if self.buffer:
                output_text += self.buffer
                self.buffer = ""

            return output_text

        except ValidationError as e:
            return f"{self.buffer}\n[VALIDATION ERROR: {str(e)}]\n"
        except Exception as e:
            return f"{self.buffer}\n[ERROR: {str(e)}]\n"

    def _parse_args(self, args_str: str) -> Dict[str, Any]:
        """
        EXACT same logic you used in your test to parse function call arguments.
        e.g. parse shell("df -h") => positional_args=["df -h"]
        """
        result = {"positional_args": []}
        parts = []
        current = []
        in_quotes = False
        quote_char = None

        for char in args_str:
            if char in ('"', "'"):
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    in_quotes = False
                current.append(char)
            elif char == ',' and not in_quotes:
                parts.append(''.join(current).strip())
                current = []
            else:
                current.append(char)
        if current:
            parts.append(''.join(current).strip())

        for i, part in enumerate(parts):
            part_stripped = part.strip()
            if '=' in part_stripped:
                key, val = part_stripped.split('=', 1)
                key = key.strip()
                val = val.strip().strip('"\'')
                result[key] = val
            else:
                val = part_stripped.strip('"\'')
                result["positional_args"].append(val)

        return result

    def _format_tool_call(self, func_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Format and validate tool calls."""
        mapped_tool = self.TOOL_NAME_MAP.get(func_name, func_name)
        
        tool_call = {
            "tool": mapped_tool,
            "input_schema": {}
        }

        pos_args = args.get("positional_args", [])

        try:
            if mapped_tool == "file":
                operation = "read"  # default

                # If first pos arg is a known file operation like "list_dir",
                # then take that as the operation, and shift the args.
                if len(pos_args) > 0 and pos_args[0] in ["read", "write", "delete", "list_dir", "append"]:
                    operation = pos_args[0]
                    pos_args = pos_args[1:]

                if "write" in func_name:
                    operation = "write"
                elif "delete" in func_name:
                    operation = "delete"

                input_schema = {
                    "operation": operation,
                    "path": pos_args[0] if pos_args else "",
                }
                if operation == "write" and len(pos_args) > 1:
                    input_schema["content"] = pos_args[1]
                
            elif mapped_tool == "code_runner":
                # Format code runner calls
                code_str = pos_args[0] if pos_args else ""
                input_schema = {
                    "files": [{"path": "main.py", "content": code_str}],
                    "main_file": "main.py",
                    "language": args.get("language", "python")
                }
                
            elif mapped_tool == "shell":
                # Format shell commands
                input_schema = {
                    "command": pos_args[0] if pos_args else ""
                }

            elif mapped_tool == "web_search":
                # Format web search queries
                input_schema = {
                    "query": pos_args[0] if pos_args else "",
                    "max_results": int(args.get("max_results", 5))
                }

            elif mapped_tool == "web_browser":
                extract_links_val = args.get("extract_links", False)
                # Convert string "False" => False, "True" => True
                if isinstance(extract_links_val, str):
                    extract_links_val = (extract_links_val.lower() == "true")

                input_schema = {
                    "url": pos_args[0] if pos_args else "",
                    "extract_type": "links" if extract_links_val else "text"
                }

            elif mapped_tool == "documentation_check":
                # Format documentation check
                input_schema = {
                    "path": pos_args[0] if pos_args else ""
                }

            elif mapped_tool == "http_request":
                # Format HTTP requests
                input_schema = {
                    "method": pos_args[0] if pos_args else "GET",
                    "url": pos_args[1] if len(pos_args) > 1 else ""
                }

            elif mapped_tool == "package_manager":
                # Format package manager commands
                input_schema = {
                    "action": pos_args[0] if pos_args else "list",
                    "package": pos_args[1] if len(pos_args) > 1 else ""
                }

            elif mapped_tool == "memory":
                # Format memory operations
                operation = "read"  # default
                if "write" in func_name:
                    operation = "write"
                elif "list" in func_name:
                    operation = "list"

                input_schema = {
                    "operation": operation,
                    "key": pos_args[0] if pos_args else "",
                }
                if operation == "write" and len(pos_args) > 1:
                    input_schema["value"] = pos_args[1]

            else:
                # For any other tool, pass args directly
                input_schema = {k: v for k, v in args.items() if k != "positional_args"}
                if pos_args:
                    input_schema["args"] = pos_args

            # Validate before returning
            self.validate_input(mapped_tool, input_schema)
            tool_call["input_schema"] = input_schema
            
            return tool_call
            
        except (IndexError, KeyError, TypeError) as e:
            raise ValidationError(
                f"Error formatting tool call for '{mapped_tool}': {str(e)}",
                {"error_type": type(e).__name__}
            )
