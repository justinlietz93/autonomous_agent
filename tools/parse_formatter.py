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

    # Will catch function calls like file_write("path","""Multi line content """)
    FUNCTION_REGEX = re.compile(r'(^|[\s\.\,\;\:\!])(\w+)\s*\(',flags=re.DOTALL)

    def __init__(self, tool_functions: Dict[str, Any], marker: str = "TOOL_CALL:", bypass_formatter: bool = False):
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
        self.bypass_formatter = bypass_formatter

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
        if self.bypass_formatter:
            return self.rtp.feed(text_chunk)

        self.buffer += text_chunk
        output_text = ""

        # Continue processing until the buffer no longer yields any new tool call markers.
        while True:
            new_output = ""
            while True:
                match = self.FUNCTION_REGEX.search(self.buffer)
                if not match:
                    break

                func_name = match.group(2)
                if func_name not in self.TOOL_NAME_MAP:
                    new_output += self.buffer[:match.end()]
                    self.buffer = self.buffer[match.end():]
                    continue

                start_index = match.start(2)
                i = match.end(0)
                paren_level = 1
                in_quote = False
                triple_quote = False
                quote_delim = ""
                escape = False

                # Process until the closing parenthesis is found.
                while i < len(self.buffer) and paren_level > 0:
                    ch = self.buffer[i]
                    if escape:
                        escape = False
                        i += 1
                        continue
                    if not in_quote:
                        if self.buffer[i:i+3] in ('"""', "'''"):
                            in_quote = True
                            triple_quote = True
                            quote_delim = self.buffer[i:i+3]
                            i += 3
                            continue
                        elif ch in ('"', "'"):
                            in_quote = True
                            triple_quote = False
                            quote_delim = ch
                            i += 1
                            continue
                        else:
                            if ch == '(':
                                paren_level += 1
                            elif ch == ')':
                                paren_level -= 1
                            i += 1
                    else:
                        if ch == '\\':
                            escape = True
                            i += 1
                        else:
                            if triple_quote and self.buffer[i:i+3] == quote_delim:
                                in_quote = False
                                triple_quote = False
                                i += 3
                            elif not triple_quote and ch == quote_delim:
                                in_quote = False
                                i += 1
                            else:
                                i += 1

                # If closing parenthesis wasn't found, break out to wait for more text.
                if paren_level != 0:
                    break

                # Extract the inline call's argument string.
                inline_call_str = self.buffer[start_index:i]
                arg_start = inline_call_str.find('(') + 1
                arg_str = inline_call_str[arg_start:-1]

                try:
                    # If the argument string is extremely long, use the fallback parser directly.
                    if len(arg_str) > 100:
                        try:
                            parsed_args = self._parse_file_write_args_tokenize(arg_str)
                        except Exception as e:
                            parsed_args = {"positional_args": []}
                    else:
                        parsed_args = self._parse_args(arg_str)
                except Exception as e:
                    if func_name.lower() == "file_write":
                        try:
                            parsed_args = self._parse_file_write_args_tokenize(arg_str)
                        except Exception as e2:
                            parsed_args = {"positional_args": []}
                    else:
                        raise e
                tool_call_json = self._format_tool_call(func_name, parsed_args)
                tool_call_str = self.marker + json.dumps(tool_call_json)
                result = self.rtp.feed(tool_call_str)


                # Replace the inline call text with the result.
                new_output += self.buffer[:start_index] + result
                self.buffer = self.buffer[i:]
            
            new_output += self.buffer
            self.buffer = ""
            # If the new output still contains a tool call marker, reassign it to buffer and process again.
            if self.marker in new_output:
                self.buffer = new_output
                output_text = ""
                continue
            else:
                output_text = new_output
                break

        return output_text

    def _parse_args(self, args_str: str) -> Dict[str, Any]:
        import ast
        try:
            # Wrap the arguments in a dummy function call.
            call_str = f"f({args_str})"
            node = ast.parse(call_str, mode='eval')
            if not (isinstance(node, ast.Expression) and isinstance(node.body, ast.Call)):
                raise ValidationError("Failed to parse arguments", {"error": "Not a function call structure"})
            call_node = node.body
            positional_args = [ast.literal_eval(arg) for arg in call_node.args]
            kwargs = {keyword.arg: ast.literal_eval(keyword.value) for keyword in call_node.keywords}
            return {"positional_args": positional_args, **kwargs}
        except Exception as e:
            raise ValidationError("Failed to parse arguments", {"error": str(e)})

    def _format_tool_call(self, func_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        mapped_tool = self.TOOL_NAME_MAP.get(func_name, func_name)
        tool_call = {"tool": mapped_tool, "input_schema": {}}
        pos_args = args.get("positional_args", [])
        try:
            if mapped_tool == "file":
                operation = "read"
                if len(pos_args) > 0 and pos_args[0] in ["read", "write", "delete", "list_dir", "append"]:
                    operation = pos_args[0]
                    pos_args = pos_args[1:]
                if "write" in func_name:
                    operation = "write"
                elif "delete" in func_name:
                    operation = "delete"
                input_schema = {"operation": operation, "path": pos_args[0] if pos_args else ""}
                if operation == "write":
                    if len(pos_args) > 1:
                        input_schema["content"] = pos_args[1]
                    else:
                        raise ValidationError("content is required for write operation")
            elif mapped_tool == "code_runner":
                code_str = pos_args[0] if pos_args else ""
                input_schema = {"files": [{"path": "main.py", "content": code_str}],
                                "main_file": "main.py",
                                "language": args.get("language", "python")}
            elif mapped_tool == "shell":
                input_schema = {"command": pos_args[0] if pos_args else ""}
            elif mapped_tool == "web_search":
                input_schema = {"query": pos_args[0] if pos_args else "",
                                "max_results": int(args.get("max_results", 5))}
            elif mapped_tool == "web_browser":
                extract_links_val = args.get("extract_links", False)
                if isinstance(extract_links_val, str):
                    extract_links_val = (extract_links_val.lower() == "true")
                input_schema = {"url": pos_args[0] if pos_args else "",
                                "extract_type": "links" if extract_links_val else "text"}
            elif mapped_tool == "documentation_check":
                input_schema = {"path": pos_args[0] if pos_args else ""}
            elif mapped_tool == "http_request":
                input_schema = {"method": pos_args[0] if pos_args else "GET",
                                "url": pos_args[1] if len(pos_args) > 1 else ""}
            elif mapped_tool == "package_manager":
                input_schema = {"action": pos_args[0] if pos_args else "list",
                                "package": pos_args[1] if len(pos_args) > 1 else ""}
            elif mapped_tool == "memory":
                operation = "read"
                if "write" in func_name:
                    operation = "write"
                elif "list" in func_name:
                    operation = "list"
                input_schema = {"operation": operation, "key": pos_args[0] if pos_args else ""}
                if operation == "write" and len(pos_args) > 1:
                    input_schema["value"] = pos_args[1]
            else:
                input_schema = {k: v for k, v in args.items() if k != "positional_args"}
                if pos_args:
                    input_schema["args"] = pos_args
            self.validate_input(mapped_tool, input_schema)
            tool_call["input_schema"] = input_schema
            return tool_call
        except (IndexError, KeyError, TypeError) as e:
            raise ValidationError(
                f"Error formatting tool call for '{mapped_tool}': {str(e)}",
                {"error_type": type(e).__name__}
            )

    def _parse_file_write_args_tokenize(self, args_str: str) -> Dict[str, Any]:
        """
        Fallback parser for file_write calls using Python's tokenize module.
        It extracts all string tokens from the argument string.
        Assumes the first string token is the file path and all subsequent tokens,
        concatenated together, form the file content.
        """
        import tokenize
        import io
        import ast

        tokens = tokenize.generate_tokens(io.StringIO(args_str).readline)
        string_literals = []
        for token_type, token_string, _, _, _ in tokens:
            if token_type == tokenize.STRING:
                try:
                    # Convert the token to its literal value.
                    value = ast.literal_eval(token_string)
                    string_literals.append(value)
                except Exception:
                    pass

        if len(string_literals) < 2:
            raise ValidationError("Failed to parse file_write arguments using tokenize", {"args_str": args_str})

        file_path = string_literals[0]
        # Join all remaining tokens to form the file content.
        file_content = "".join(string_literals[1:])
        return {"positional_args": [file_path, file_content]}
