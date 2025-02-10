# real_time_tool_parser.py

#########################################################

# WARNING: THIS FILE IS OFF LIMITS. IT IS COMPLETED AND 
# SHOULD NOT BE MODIFIED.

#########################################################   

import json
import inspect
import typing
from datetime import datetime
import re
from typing import List, Dict, Any, Optional

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

    Features:
    - Rolling buffer so "TOOL_CALL:" can be detected even if split across chunks.
    - Deferred JSON capture that starts at the first '{' after the marker.
    - Brace-depth tracking to find the complete JSON block.
    - Basic type-checking using Python function type hints.
    - A history log of all calls/results for potential debugging or persistence.
    - Optionally streams results back into the conversation context.
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

        # Rolling buffer for partial marker detection
        self._last_chars = ""

        # Buffers/states for parsing incremental JSON
        self._json_buffer = ""
        self._parsing_json = False
        self._brace_depth = 0
        self._in_string = False
        self._escape_next = False

        # For capturing recent text (for error context)
        self._recent_context = ""

        # History of calls (and results) for debugging or advanced agent usage
        self.history = []

        # Count consecutive failures to avoid infinite retry loops
        self.consecutive_failures = 0

    def feed(self, text_chunk: str) -> str:
        """
        Main entry point: feed the next chunk of text from the LLM.
        Returns any normal text (i.e., not tool calls) to be passed on
        to the user or conversation. If a tool call is encountered,
        it is executed immediately in this method.

        If a call fails validation or execution, raises ToolCallError with
        a snippet of context. The caller can catch it and feed that error
        back to the LLM to let the model self-correct.
        """
        output_to_user = ""
        output_to_user = "" # Initialize output_to_user to empty string at the very beginning
        if self._parsing_json:
            output_to_user = "" # Initialize to empty string when parsing JSON

        # Update recent context (for debugging or error messages), trimmed to context_window
        self._recent_context += text_chunk
        if len(self._recent_context) > self.context_window:
            self._recent_context = self._recent_context[-self.context_window:]

        if self._parsing_json:
            # Continue capturing an in-progress JSON block from a previous chunk
            for i, ch in enumerate(text_chunk):
                self._accumulate_json_char(ch)
                if not self._parsing_json:
                    # JSON completed in the middle of this chunk
                    self._handle_complete_tool_call()
                    # We might have leftover text after the JSON ends
                    leftover = text_chunk[i + 1:]
                    output_to_user += self.feed(leftover)
                    return output_to_user
            # If we reach here, still in JSON parse mode. Return whatever normal text preceded the marker.
            return output_to_user

        # If we're NOT currently parsing JSON, search for the marker in (last_chars + current chunk)
        combined_text = self._last_chars + text_chunk
        idx = combined_text.find(self.marker)
        if idx == -1:
            safe_output = combined_text # Simply output the entire combined_text
            start_idx = len(self._last_chars)
            output_to_user += safe_output[start_idx:]
            self._last_chars = "" # Reset last_chars since we've processed everything
            return output_to_user

        # If marker is found
        marker_pos_in_combined = idx
        marker_pos_in_chunk = marker_pos_in_combined - len(self._last_chars)
        output_to_user = "" # Initialize output_to_user to empty string here
        if marker_pos_in_chunk < 0:
            marker_pos_in_chunk = 0

        # Output everything before the marker
        output_to_user += combined_text[:marker_pos_in_combined][len(self._last_chars):]

        # Everything after that remains to be processed for JSON capture
        after_marker_index = idx + len(self.marker)

        # Discard the portion up to the marker from the combined_text => we keep only remainder
        remainder = combined_text[after_marker_index:]

        # Skip any whitespace after the marker
        brace_index = 0
        while brace_index < len(remainder) and remainder[brace_index].isspace():
            brace_index += 1

        if brace_index >= len(remainder):
            # We have a marker with no JSON start in this chunk
            self._parsing_json = True
            self._brace_depth = 0
            self._in_string = False
            self._escape_next = False
            self._json_buffer = ""
            self._last_chars = combined_text[idx:]  # store the partial marker + any trailing space
            return output_to_user

        if remainder[brace_index] != '{':
            # The next non-space char after "TOOL_CALL:" wasn't '{' => malformed call
            raise ToolCallError(
                "Malformed tool call: expected '{' after marker",
                context=self._recent_context
            )

        # Begin JSON parsing
        self._parsing_json = True
        output_to_user = "" # Return empty string from this point when parsing JSON starts

        self._brace_depth = 0
        self._in_string = False
        self._escape_next = False
        self._json_buffer = ""

        # Accumulate from the '{' onward
        for i, ch in enumerate(remainder[brace_index:]):
            self._accumulate_json_char(ch)
            if not self._parsing_json:
                # JSON finished inside this chunk
                consumed_up_to = brace_index + i + 1
                leftover_chunk = remainder[consumed_up_to:]
                self._handle_complete_tool_call()
                output_to_user += self.feed(leftover_chunk)
                return output_to_user

        # If we get here, we didn't finish JSON in this chunk
        self._last_chars = ""
        output_to_user = "" # Force empty output when marker is found, right before return
        return output_to_user

    def _accumulate_json_char(self, ch: str):
        """
        Track a single character as part of an in-progress JSON object.
        Uses brace depth and string-literal state to decide when the JSON is complete.
        """
        self._json_buffer += ch

        if self._in_string:
            if self._escape_next:
                self._escape_next = False
            else:
                if ch == '\\':
                    self._escape_next = True
                elif ch == '"':
                    self._in_string = False
            return

        if ch == '"':
            self._in_string = True
            self._escape_next = False
            return
        elif ch == '{':
            self._brace_depth += 1
        elif ch == '}':
            if self._brace_depth > 0:
                self._brace_depth -= 1
            if self._brace_depth == 0:
                # JSON block completed
                self._parsing_json = False

    def _handle_complete_tool_call(self):
        """
        We have a complete JSON block in self._json_buffer. 
        Validate, call the appropriate tool, log or raise errors.
        """
        full_json = self._json_buffer
        self._json_buffer = ""

        # Also clear out the rolling marker buffer, since we've used it
        self._last_chars = ""

        try:
            call_data = json.loads(full_json)
        except json.JSONDecodeError as e:
            raise ToolCallError(
                f"JSON parse error: {e}",
                context=self._recent_context
            )

        if not isinstance(call_data, dict):
            raise ToolCallError(
                "Tool call JSON must be a top-level object/dict.",
                context=self._recent_context
            )

        # Check required top-level fields
        if "tool" not in call_data or "input_schema" not in call_data:
            raise ToolCallError(
                "Invalid tool call: must have 'tool' and 'input_schema' fields.",
                context=self._recent_context
            )

        tool_name = call_data["tool"]
        inputs = call_data["input_schema"]

        if tool_name not in self.tools:
            raise ToolCallError(
                f"Unrecognized tool '{tool_name}'",
                context=self._recent_context
            )

        if not isinstance(inputs, dict):
            raise ToolCallError(
                "input_schema must be an object/dict",
                context=self._recent_context
            )

        tool_object = self.tools[tool_name]

        # Signature check on the run method
        sig = inspect.signature(tool_object.run)
        try:
            sig.bind(input=inputs)  # Validate against run method's signature
        except TypeError as te:
            raise ToolCallError(
                f"Tool call argument mismatch: {te}",
                context=self._recent_context
            )

        # Execute the tool's run method
        try:
            result = tool_object.run(input=inputs)
            
            # Log success
            self.history.append({
                "time": datetime.now().isoformat(),
                "tool": tool_name,
                "input": inputs,
                "output": result,
                "status": "successfully called tool"
            })

            # Format and return the result
            if isinstance(result, dict):
                if 'content' in result:
                    return str(result['content'])
                elif 'output' in result:
                    return str(result['output'])
            return str(result)

        except Exception as ex:
            raise ToolCallError(
                f"Tool '{tool_name}' execution failed: {ex}",
                context=self._recent_context
            )

    def get_history(self):
        """Retrieve log of tool calls (for debugging or storing in a DB)."""
        
        print(f"DEBUG: self.history = {self.history}")
        return list(self.history)

    def reset(self):
        """
        Reset parser state between conversations or whenever needed.
        """
        self._last_chars = ""
        self._json_buffer = ""
        self._parsing_json = False
        self._brace_depth = 0
        self._in_string = False
        self._escape_next = False
        self._recent_context = ""
        self.history.clear()
        self.consecutive_failures = 0

    def debug_mode(self, enabled: bool = True) -> None:
        """Enable/disable debug logging"""
        self._debug = enabled

def parse_tool_calls(text: str) -> List[Dict[str, Any]]:
    """Parse tool calls from streamed text output."""
    # Static buffer to accumulate text across calls
    if not hasattr(parse_tool_calls, '_buffer'):
        parse_tool_calls._buffer = ''
    
    # Add new text to buffer
    parse_tool_calls._buffer += text
    
    print(f"DEBUG: Current buffer: {repr(parse_tool_calls._buffer)}")  # Debug line
    
    # Look for complete tool calls
    tool_calls = []
    
    marker = 'TOOL_CALL:'
    
    while marker in parse_tool_calls._buffer:
        try:
            start = parse_tool_calls._buffer.index(marker)
            json_start = parse_tool_calls._buffer.index('{', start)
            
            print(f"DEBUG: Found tool call at {start}, JSON starts at {json_start}")  # Debug line
            print(f"DEBUG: JSON content: {repr(parse_tool_calls._buffer[json_start:])}")  # Debug line
            
            # Track nested braces to find complete JSON
            brace_count = 0
            in_string = False
            escape_next = False
            
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
                            # Found complete JSON
                            json_str = parse_tool_calls._buffer[json_start:i+1]
                            try:
                                tool_call = json.loads(json_str)
                                if "tool" in tool_call and "input_schema" in tool_call:
                                    tool_calls.append(tool_call)
                            except json.JSONDecodeError:
                                pass  # Skip invalid JSON
                            
                            # Remove processed part from buffer
                            parse_tool_calls._buffer = parse_tool_calls._buffer[i+1:]
                            break
            
            if brace_count > 0:
                # Incomplete JSON, keep buffering
                break
                
            # Remove processed part up to json_start if no valid JSON found
            parse_tool_calls._buffer = parse_tool_calls._buffer[json_start:]
            
        except ValueError:
            # No complete tool call found
            break
            
    return tool_calls