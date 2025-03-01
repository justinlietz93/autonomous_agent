# tool_parser.py

#########################################################

# WARNING: 
# IF YOU FIND ISSUES DOCUMENT THEM IN docs/tool_pipeline_issues.md

#########################################################   

import json
import inspect
import typing
from datetime import datetime
import re
from typing import List, Dict, Any, Optional, Union
import time

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

        # Add timeout check
        self.last_json_activity = time.time()

        # Add a new state
        self._waiting_for_json_start = False

    def feed(self, text_chunk: str) -> str:
        # Add buffer size safety check
        if self._parsing_json and len(self._json_buffer) > 100000:  # 100KB max
            print("Warning: JSON buffer size exceeded limits, resetting parser state")
            self._parsing_json = False
            self.reset()
        
        # Change timeout to only start when we've received the opening brace
        if self._parsing_json and self._json_buffer and time.time() - self.last_json_activity > 5.0:
            # Only timeout if we've already started receiving actual JSON
            print("Warning: JSON parsing timeout, resetting state")
            self._parsing_json = False
            self.reset()
        
        output_to_user = ""
        if self._parsing_json:
            for i, ch in enumerate(text_chunk):
                self._accumulate_json_char(ch)
                if not self._parsing_json:
                    tool_result = self._handle_complete_tool_call()
                    output_to_user += tool_result
                    leftover = text_chunk[i + 1:]
                    output_to_user += self.feed(leftover)
                    return output_to_user
            return output_to_user

        # Update recent context (for debugging or error messages)
        self._recent_context += text_chunk
        if len(self._recent_context) > self.context_window:
            self._recent_context = self._recent_context[-self.context_window:]

        # Combine any leftover partial marker with the current chunk
        combined_text = self._last_chars + text_chunk
        idx = combined_text.find(self.marker)
        
        if idx == -1:
            # Check if the end of combined_text could be the start of a marker.
            partial_marker_length = 0
            for i in range(1, len(self.marker)):
                if combined_text.endswith(self.marker[:i]):
                    partial_marker_length = i
                    break
            # Output everything except the potential partial marker.
            safe_output = combined_text[:-partial_marker_length] if partial_marker_length else combined_text
            # Save the partial marker for the next chunk.
            self._last_chars = combined_text[-partial_marker_length:] if partial_marker_length else ""
            output_to_user += safe_output
            return output_to_user

        # If marker is found:
        marker_pos_in_combined = idx
        marker_pos_in_chunk = marker_pos_in_combined - len(self._last_chars)
        if marker_pos_in_chunk >= 0:
            output_to_user += text_chunk[:marker_pos_in_chunk]

        # Reset the partial marker buffer as we've now found a complete marker.
        self._last_chars = ""
        
        # Start JSON parsing mode.
        self._parsing_json = True
        self._json_buffer = ""
        self._brace_depth = 0

        # Process remaining text after the marker.
        remaining = text_chunk[marker_pos_in_chunk + len(self.marker):]
        if remaining:
            result = self.feed(remaining)
            output_to_user += result

        # If we're waiting for JSON to start, look for the opening brace
        if self._waiting_for_json_start:
            for i, ch in enumerate(text_chunk):
                if ch == '{':
                    self._waiting_for_json_start = False
                    self._parsing_json = True
                    self._accumulate_json_char(ch)
                    # Process rest of chunk
                    leftover = text_chunk[i+1:]
                    return self.feed(leftover)

        return output_to_user


    def _accumulate_json_char(self, ch: str):
        """
        Track a single character as part of an in-progress JSON object.
        Uses brace depth and string-literal state to decide when the JSON is complete.
        """
        self._json_buffer += ch
        # Update activity timestamp whenever we're still getting characters
        self.last_json_activity = time.time()

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

    def _handle_complete_tool_call(self) -> str:
        """
        We have a complete JSON block in self._json_buffer. 
        Validate, call the appropriate tool, log or raise errors.
        """
        full_json = self._json_buffer
        self._json_buffer = ""

        # Also clear out the rolling marker buffer, since we've used it
        self._last_chars = ""

        try:
            # Parse the JSON
            try:
                tool_call = json.loads(full_json)
            except json.JSONDecodeError as e:
                return f"[TOOL_CALL ERROR: Invalid JSON: {e}]"
            
            # Extract tool name and parameters
            tool_name = tool_call.get("tool")
            if not tool_name:
                return "[TOOL_CALL ERROR: Missing 'tool' field]"
            
            # Map function-style names to actual tool names
            # For example, map "file_read" to "file"
            TOOL_NAME_MAP = {
                "file_read": "file",
                "file_write": "file",
                "file_delete": "file",
                "file_append": "file",
                "file_list_dir": "file",
                "shell": "shell",
                "code_runner": "code_runner",
                "web_search": "web_search",
                "web_browser": "web_browser",
                "http_request": "http_request",
                "documentation_check": "documentation_check",
                "package_manager": "package_manager"
            }
            
            # Apply mapping if needed
            mapped_tool_name = TOOL_NAME_MAP.get(tool_name, tool_name)
            
            # Get the tool
            tool = self.tools.get(mapped_tool_name)
            if not tool:
                return f"[TOOL_CALL ERROR: Unrecognized tool '{tool_name}']"

            # Signature check on the run method
            sig = inspect.signature(tool.run)
            try:
                sig.bind(input=tool_call["input_schema"])  # Validate against run method's signature
            except TypeError as te:
                return f"[TOOL_CALL ERROR: Tool call argument mismatch: {te}]"

            # Execute the tool's run method
            try:
                result = tool.run(input=tool_call["input_schema"])
                
                # Log success
                self.history.append({
                    "time": datetime.now().isoformat(),
                    "tool": mapped_tool_name,
                    "input": tool_call["input_schema"],
                    "output": result,
                    "status": "successfully called tool"
                })

                # Extract string result
                if isinstance(result, dict):
                    return f"\n{result.get('content', '')}\n"
                return str(result)  # Convert any other result to string

            except Exception as ex:
                return f"[TOOL_CALL ERROR: Tool '{mapped_tool_name}' execution failed: {ex}]"

        except Exception as ex:
            return f"[TOOL_CALL ERROR: General error: {ex}]"

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

        # Reset timeout
        self.last_json_activity = time.time()

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