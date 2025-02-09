import re
import json
from typing import Any, Dict

from tools.tool_parser import RealTimeToolParser, ToolCallError

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
        "package_manager": "package_manager"
        # Add more if needed
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

    def feed(self, text_chunk: str) -> str:
        """
        1) Accumulate chunk into self.buffer
        2) Scan for inline calls like shell("args..."), turning them into
           'TOOL_CALL: { "tool":..., "input_schema": {...}}'
        3) Let the RealTimeToolParser handle those newly embedded JSON calls
        4) Return the normal text (non-tool) that remains
        """
        self.buffer += text_chunk
        output_text = ""

        while True:
            # Look for something like shell(...). We’ll do a simple pattern: (\w+)\(.*?\)
            # but we need balanced parentheses. A simpler approach is to find functionName(
            # then parse until we reach the matching closing parenthesis at the same level.
            match = re.search(r'(\w+)\(', self.buffer)
            if not match:
                # No more inline calls in the buffer. We'll pass everything to parser at once.
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

        # After substituting all inline calls, pass the entire thing to RealTimeToolParser
        # The parser returns only the normal text. We keep the leftover buffer for next feed.
        # But we need to feed both output_text + leftover buffer? Actually let's do:
        # 1) We'll combine them
        combined_text = output_text + self.buffer
        self.buffer = ""  # we now hand everything to the real parser

        # Now let RealTimeToolParser handle any "TOOL_CALL: { ... }" or leftover
        result_text = ""
        try:
            result_text = self.rtp.feed(combined_text)
        except ToolCallError as e:
            # Optionally handle or raise
            raise e

        return result_text

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
        """
        EXACT same logic to map inline calls to structured input_schema.
        e.g. shell(...) => {"tool": "shell", "input_schema": {...}}
        """
        # Step 1: map the function name
        mapped_tool = self.TOOL_NAME_MAP.get(func_name, func_name)

        # Build the JSON
        tool_call = {
            "tool": mapped_tool,
            "input_schema": {}
        }

        pos_args = args.get("positional_args", [])

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
            content = pos_args[1] if len(pos_args) > 1 else ""

            tool_call["input_schema"] = {
                "operation": operation,
                "path": path,
                "content": content
            }

        elif mapped_tool == "code_runner":
            code_str = pos_args[0] if len(pos_args) > 0 else ""
            language = args.get("language", "python")
            tool_call["input_schema"] = {
                "files": [{"path": "main.py", "content": code_str}],
                "main_file": "main.py",
                "language": language
            }

        elif mapped_tool == "shell":
            command_str = pos_args[0] if len(pos_args) > 0 else ""
            tool_call["input_schema"] = {"command": command_str}

        elif mapped_tool == "documentation_check":
            path_str = pos_args[0] if len(pos_args) > 0 else ""
            tool_call["input_schema"] = {"path": path_str}

        elif mapped_tool == "web_search":
            query = pos_args[0] if len(pos_args) > 0 else ""
            max_results = int(args.get("max_results", 5))
            tool_call["input_schema"] = {
                "query": query,
                "max_results": max_results
            }

        elif mapped_tool == "web_browser":
            url = pos_args[0] if len(pos_args) > 0 else ""
            extract_links = args.get("extract_links", False)
            tool_call["input_schema"] = {
                "url": url,
                "extract_type": "links" if extract_links else "text"
            }

        elif mapped_tool == "http_request":
            method = pos_args[0] if len(pos_args) > 0 else "GET"
            url = pos_args[1] if len(pos_args) > 1 else ""
            tool_call["input_schema"] = {
                "method": method,
                "url": url
            }

        elif mapped_tool == "package_manager":
            action = pos_args[0] if len(pos_args) > 0 else "install"
            package = pos_args[1] if len(pos_args) > 1 else ""
            tool_call["input_schema"] = {
                "action": action,
                "package": package
            }

        else:
            # default
            tool_call["input_schema"] = args

        return tool_call
