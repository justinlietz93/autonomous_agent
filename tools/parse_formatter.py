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

    def feed(self, text_chunk: str) -> str:
        """
        1) Accumulate chunk into self.buffer
        2) Scan for inline calls like shell(...), turning them into
           'TOOL_CALL: { "tool":..., "input_schema": {...}}'
        3) Let the RealTimeToolParser handle those newly embedded JSON calls
        4) Return the normal text (non-tool) that remains
        """
        try:
            self.buffer += text_chunk
            output_text = ""

            while True:
                match = re.search(r'(\w+)\(', self.buffer)
                if not match:
                    break

                func_name = match.group(1)  # e.g. "shell"
                start_index = match.start()

                # We want to find the matching closing parenthesis. We'll track nesting level
                paren_level = 1
                i = match.end()
                while i < len(self.buffer) and paren_level > 0:
                    if self.buffer[i] == '(':
                        paren_level += 1
                    elif self.buffer[i] == ')':
                        paren_level -= 1
                    i += 1

                if paren_level != 0:
                    # We didn't find a matching ')', means we need more text
                    # So we just return for now; we'll parse more on the next chunk
                    return ""

                # We have the entire substring: funcName(...) from start_index to i
                inline_call_str = self.buffer[start_index:i]
                # The arguments are inside the parentheses
                arg_str = inline_call_str[len(func_name)+1 : -1]  # remove "foo(" and the final ")"

                # Build a function to parse those arguments
                parsed_args = self._parse_args(arg_str)

                # Map the function name to the actual tool, build input_schema
                tool_call_json = self._format_tool_call(func_name, parsed_args)

                # Turn it into a 'TOOL_CALL: {...}' string
                # We'll replace the entire inline call with that
                new_tool_call_str = self.marker + json.dumps(tool_call_json, ensure_ascii=False)

                # Everything up to the start of the match is normal text
                output_text += self.buffer[:start_index]

                # Insert the 'TOOL_CALL: ...'
                output_text += new_tool_call_str

                # Remove that portion from self.buffer
                self.buffer = self.buffer[i:]

            # After processing all tool calls, combine remaining text
            combined_text = output_text + self.buffer
            
            # Clear buffer only after successful processing
            self.buffer = ""
            
            # Process through RealTimeToolParser
            try:
                result_text = self.rtp.feed(combined_text)
                return result_text
            except ToolCallError as e:
                # Return both the error and the original text
                return f"{combined_text}\n[TOOL ERROR: {str(e)}]\n"
                
        except ValidationError as e:
            # Return both the error and any accumulated text
            return f"{self.buffer}\n[VALIDATION ERROR: {str(e)}]\n"
        except Exception as e:
            # Return both the error and any accumulated text
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
                if "write" in func_name:
                    operation = "write"
                elif "read" in func_name:
                    operation = "read"
                elif "list_dir" in func_name:
                    operation = "list_dir"
                else:
                    operation = "delete"
                path = pos_args[0] if len(pos_args) > 0 else ""
                content = pos_args[1] if len(pos_args) > 1 and operation == "write" else ""

                input_schema = {
                    "operation": operation,
                    "path": path,
                    "content": content
                }
                
            elif mapped_tool == "code_runner":
                code_str = pos_args[0] if len(pos_args) > 0 else ""
                language = args.get("language", "python")
                input_schema = {
                    "files": [{"path": "main.py", "content": code_str}],
                    "main_file": "main.py",
                    "language": language
                }
                
            elif mapped_tool == "shell":
                command_str = pos_args[0] if len(pos_args) > 0 else ""
                input_schema = {"command": command_str}

            elif mapped_tool == "documentation_check":
                path_str = pos_args[0] if len(pos_args) > 0 else ""
                input_schema = {"path": path_str}

            elif mapped_tool == "web_search":
                query = pos_args[0] if len(pos_args) > 0 else ""
                max_results = int(args.get("max_results", 5))
                input_schema = {
                    "query": query,
                    "max_results": max_results
                }

            elif mapped_tool == "web_browser":
                url = pos_args[0] if len(pos_args) > 0 else ""
                extract_links = args.get("extract_links", False)
                input_schema = {
                    "url": url,
                    "extract_type": "links" if extract_links else "text"
                }

            elif mapped_tool == "http_request":
                method = pos_args[0] if len(pos_args) > 0 else "GET"
                url = pos_args[1] if len(pos_args) > 1 else ""
                input_schema = {
                    "method": method,
                    "url": url
                }

            elif mapped_tool == "package_manager":
                action = pos_args[0] if len(pos_args) > 0 else "install"
                package = pos_args[1] if len(pos_args) > 1 else ""
                input_schema = {
                    "action": action,
                    "package": package
                }

            elif mapped_tool == "memory":
                if "write" in func_name:
                    operation = "write"
                elif "read" in func_name:
                    operation = "read"
                else:
                    operation = "list"
                    
                key = pos_args[0] if len(pos_args) > 0 else ""
                value = pos_args[1] if len(pos_args) > 1 and operation == "write" else ""
                
                input_schema = {
                    "operation": operation,
                    "key": key,
                    "value": value
                }

            else:
                # default
                input_schema = args

            # Validate the input schema before returning
            self.validate_input(mapped_tool, input_schema)
            tool_call["input_schema"] = input_schema
            
            return tool_call
            
        except (IndexError, KeyError, TypeError) as e:
            raise ValidationError(
                f"Error formatting tool call for '{mapped_tool}': {str(e)}",
                {"error_type": type(e).__name__}
            )
