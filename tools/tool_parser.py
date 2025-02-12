#########################################################
# WARNING: THIS FILE IS OFF LIMITS. IT IS COMPLETED AND 
# SHOULD NOT BE MODIFIED. DO NOT MODIFY WITHOUT EXPLICIT
# PERMISSION FROM JUSTIN.
# IF YOU FIND ISSUES DOCUMENT THEM IN docs/tool_pipeline_issues.md
#########################################################

import json
import inspect
from datetime import datetime
import re
from typing import List, Dict, Any, Optional, Tuple

class ToolCallError(Exception):
    """
    Custom exception used to signal an invalid or failed tool call.
    Contains a message and a snippet of recent context for the LLM to see.
    """
    def __init__(self, message: str, context: str):
        super().__init__(f"ToolCallError: {message}")
        self.message = message
        self.context = context

class RealTimeToolParser:
    """
    A streaming parser that:
      1. Watches incoming text chunks for the special marker "TOOL_CALL:".
      2. Collects JSON after this marker (possibly split across chunk boundaries).
      3. Validates the JSON structure & function signature.
      4. Executes the matching tool (function) immediately.
      5. Returns normal text output (non-tool text) as it arrives.
      6. Feeds errors back to the LLM if the call fails.
      
    This iterative implementation avoids deep recursion by using an internal buffer.
    """

    def __init__(
        self,
        tools: dict,
        marker: str = "TOOL_CALL:",
        context_window: int = 2500
    ):
        """
        :param tools: A dict {tool_name: callable} representing available tools.
                      Each callable should have annotated parameters for best validation.
        :param marker: The string that signals a tool call block, default 'TOOL_CALL:'.
        :param context_window: How many characters of recent context to keep for error messages.
        """
        self.tools = tools
        self.marker = marker
        self.context_window = context_window
        self._debug = False

        # Persistent internal buffer for accumulating text
        self._buffer = ""

        # Recent context for error reporting
        self._recent_context = ""

        # History of calls (and results) for debugging or advanced agent usage
        self.history = []

        # Count consecutive failures to avoid infinite retry loops
        self.consecutive_failures = 0

    def feed(self, text_chunk: str) -> str:
        """
        Append a new text chunk to the internal buffer and process it iteratively.
        Returns the text output with tool calls replaced by their results.
        """
        output_to_user = ""
        self._buffer += text_chunk

        # Update recent context (for error messages)
        self._recent_context += text_chunk
        if len(self._recent_context) > self.context_window:
            self._recent_context = self._recent_context[-self.context_window:]

        while True:
            # Look for the marker in the current buffer.
            marker_idx = self._buffer.find(self.marker)
            if marker_idx == -1:
                # No marker found.
                # Check if the end of the buffer might be a partial marker.
                partial_marker_length = 0
                for i in range(1, len(self.marker)):
                    if self._buffer.endswith(self.marker[:i]):
                        partial_marker_length = i
                        break
                safe_output = self._buffer[:-partial_marker_length] if partial_marker_length else self._buffer
                output_to_user += safe_output
                self._buffer = self._buffer[-partial_marker_length:] if partial_marker_length else ""
                break
            else:
                # Output text before the marker.
                output_to_user += self._buffer[:marker_idx]
                # Remove the text up to (and including) the marker.
                self._buffer = self._buffer[marker_idx + len(self.marker):]

                # Attempt to extract a complete JSON block from the buffer.
                json_block, remaining = self._extract_complete_json(self._buffer)
                if json_block is None:
                    # Incomplete JSON block—wait for more text.
                    break
                else:
                    self._buffer = remaining
                    try:
                        tool_call = json.loads(json_block)
                        tool_result = self._execute_tool_call(tool_call)
                        output_to_user += tool_result
                    except Exception as e:
                        output_to_user += f"[Error processing tool call: {e}]"
                    # Continue processing any remaining text in the buffer.

        return output_to_user

    def _extract_complete_json(self, buffer: str) -> Tuple[Optional[str], str]:
        """
        Attempt to extract a complete JSON block from the beginning of the buffer.
        Returns a tuple: (json_block, remaining_buffer). If no complete block is found,
        returns (None, buffer).
        """
        start_idx = buffer.find('{')
        if start_idx == -1:
            return None, buffer

        in_string = False
        escape_next = False
        brace_count = 0
        json_end_idx = None

        for i in range(start_idx, len(buffer)):
            ch = buffer[i]
            if escape_next:
                escape_next = False
                continue
            if ch == '\\':
                escape_next = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if not in_string:
                if ch == '{':
                    brace_count += 1
                elif ch == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end_idx = i
                        break

        if json_end_idx is not None:
            json_block = buffer[start_idx:json_end_idx+1]
            remaining = buffer[json_end_idx+1:]
            return json_block, remaining
        else:
            return None, buffer

    def _execute_tool_call(self, tool_call: dict) -> str:
        """
        Validate and execute the tool call based on the parsed JSON.
        Returns the output of the tool as a string.
        """
        if not isinstance(tool_call, dict):
            raise ToolCallError("Tool call JSON must be a top-level object/dict.", context=self._recent_context)

        if "tool" not in tool_call or "input_schema" not in tool_call:
            raise ToolCallError("Invalid tool call: must have 'tool' and 'input_schema' fields.", context=self._recent_context)

        tool_name = tool_call["tool"]
        inputs = tool_call["input_schema"]

        if tool_name not in self.tools:
            raise ToolCallError(f"Unrecognized tool '{tool_name}'", context=self._recent_context)

        if not isinstance(inputs, dict):
            raise ToolCallError("input_schema must be an object/dict", context=self._recent_context)

        tool_object = self.tools[tool_name]
        sig = inspect.signature(tool_object.run)
        try:
            sig.bind(input=inputs)  # Validate against the run method's signature.
        except TypeError as te:
            raise ToolCallError(f"Tool call argument mismatch: {te}", context=self._recent_context)

        try:
            result = tool_object.run(input=inputs)
            # Log the successful tool call.
            self.history.append({
                "time": datetime.now().isoformat(),
                "tool": tool_name,
                "input": inputs,
                "output": result,
                "status": "successfully called tool"
            })

            # Return the result as a string.
            if isinstance(result, dict):
                return f"\n{result.get('content', '')}\n"
            return str(result)
        except Exception as ex:
            raise ToolCallError(f"Tool '{tool_name}' execution failed: {ex}", context=self._recent_context)

    def get_history(self) -> List[Dict[str, Any]]:
        """Retrieve log of tool calls (for debugging or storing in a DB)."""
        return list(self.history)

    def reset(self):
        """Reset parser state between conversations or whenever needed."""
        self._buffer = ""
        self._recent_context = ""
        self.history.clear()
        self.consecutive_failures = 0

    def debug_mode(self, enabled: bool = True) -> None:
        """Enable/disable debug logging."""
        self._debug = enabled

def parse_tool_calls(text: str) -> List[Dict[str, Any]]:
    """
    Parse tool calls from streamed text output.
    This utility function accumulates text in a static buffer and returns any complete tool call JSON blocks.
    """
    if not hasattr(parse_tool_calls, '_buffer'):
        parse_tool_calls._buffer = ''
    
    parse_tool_calls._buffer += text
    tool_calls = []
    marker = 'TOOL_CALL:'
    
    while marker in parse_tool_calls._buffer:
        try:
            start = parse_tool_calls._buffer.index(marker)
            json_start = parse_tool_calls._buffer.index('{', start)
            brace_count = 0
            in_string = False
            escape_next = False
            json_end = None
            for i, char in enumerate(parse_tool_calls._buffer[json_start:], json_start):
                if escape_next:
                    escape_next = False
                    continue
                if char == '\\':
                    escape_next = True
                    continue
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i
                            break
            if json_end is not None:
                json_str = parse_tool_calls._buffer[json_start:json_end+1]
                try:
                    tool_call = json.loads(json_str)
                    if "tool" in tool_call and "input_schema" in tool_call:
                        tool_calls.append(tool_call)
                except json.JSONDecodeError:
                    pass  # Skip invalid JSON.
                parse_tool_calls._buffer = parse_tool_calls._buffer[json_end+1:]
            else:
                break
        except ValueError:
            break
            
    return tool_calls
