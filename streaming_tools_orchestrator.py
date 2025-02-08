# file: Streaming_Tools_Orchestrator.py

import json
import time
from tools.tool_parser import RealTimeToolParser, ToolCallError
from typing import Optional, Iterator

class StreamingToolOrchestrator:
    """
    This orchestrator streams the LLM response chunk by chunk,
    passes each chunk to RealTimeToolParser, and intercepts any
    'TOOL_CALL:{...}' blocks. If found, it executes the matching
    tool from the ToolManager, so the LLM can use them in real-time.

    Usage Flow:
      1) Build an instance, passing your tool_manager and a streaming LLM call.
      2) Call orchestrator.run_streaming(llm_response_chunks) -> yields normal text
      3) The parser invokes tools as soon as it sees 'TOOL_CALL:'.
    """

    def __init__(self, tool_manager, parser_marker="TOOL_CALL:"):
        # Store your existing tool_manager with all registered Tools
        self.tool_manager = tool_manager

        # Build a dictionary {tool_name: a python callable} for the parser.
        # We want a function signature that matches how RealTimeToolParser expects to call it.
        # For each tool, we'll return a function that calls `tool.run(...)`
        self.tools_dict = {}
        for name, tool_instance in self.tool_manager.tools.items():
            # The parser expects a function with typed parameters, but we’ll just accept **kwargs
            def make_caller(tool_obj):
                def _func(**kwargs):
                    """Thin wrapper that calls the tool_obj.run(kwargs) and returns the 'content' field."""
                    # tool_obj.run(...) returns a dict with "type" and "content"
                    result = tool_obj.run(kwargs)
                    # Return a plain string or JSON so the parser can embed it in the conversation
                    return json.dumps(result, ensure_ascii=False)
                return _func
            self.tools_dict[name] = make_caller(tool_instance)

        # Create an instance of RealTimeToolParser
        self.parser = RealTimeToolParser(
            tools=self.tools_dict,
            marker=parser_marker,
            context_window=3000
        )

    def run_streaming(self, chunk_iterator: Iterator[str]) -> Iterator[str]:
        """
        Main generator that:
          - Takes an iterator of text chunks from your LLM (e.g. Ollama or OpenAI stream)
          - Feeds them to RealTimeToolParser
          - Yields normal text lines (not tool calls) back to the caller

        If a tool call is detected, RealTimeToolParser executes it immediately.
        If there's an error in the tool call, we raise a ToolCallError so the LLM
        can see it and self-correct.
        """
        for chunk in chunk_iterator:
            try:
                # Feed chunk to the parser
                user_visible_text = self.parser.feed(chunk)
                if user_visible_text:
                    yield user_visible_text
            except ToolCallError as e:
                # If there's a parse or execution error, you can handle it here.
                # E.g. raise it again or return it to the LLM for self-correction.
                # For a quick approach, let's just yield the error text to the user stream:
                error_msg = f"\n[TOOL_CALL ERROR: {e.message}]\n"
                yield error_msg
                # Optionally you might re-raise to let the LLM fix itself.
                # raise

    def get_tool_call_history(self):
        """Expose all successful tool calls from the parser's history."""
        return self.parser.get_history()

    def reset(self):
        """Reset parser state if needed between sessions."""
        self.parser.reset()
