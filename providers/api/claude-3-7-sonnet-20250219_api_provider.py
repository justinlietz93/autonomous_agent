# providers/api/claude-3-7-sonnet-20250219_api_provider.py

from typing import Dict, Any, Generator
import anthropic
import os

from tools.tool_base import Tool
from providers.api.config import Config
from providers.utils.safe_chunker import SafeChunker
from providers.utils.stream_smoother import StreamSmoother

# If you want in-line calls, import your parser
from tools.parse_formatter import InlineCallParser
# And if you have a tool_manager:
from tools.tool_manager import ToolManager

# Add this import to your provider files
from utils.connection_monitor import monitor_connection


class Claude37SonnetProvider(Tool):
    name = "claude-3-7-sonnet-20250219_api"
    description = "Provides access to Claude 3.7 Sonnet via Anthropic's API"
    input_schema = {
        "type": "object",
        "properties": {
            "messages": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Chat message history"
            },
            "max_tokens": {
                "type": "integer",
                "description": "Maximum tokens to generate",
                "default": 4096
            },
            "temperature": {
                "type": "number",
                "description": "Temperature for generation (0-1)",
                "default": 0.4
            },
            "thinking": {
                "type": "object",
                "description": "Controls thinking mode for Claude",
                "properties": {
                    "type": {"type": "string", "enum": ["enabled", "disabled"]},
                    "budget_tokens": {"type": "integer"}
                },
                "default": None
            }
        },
        "required": ["messages"]
    }

    def __init__(self, tool_manager: ToolManager = None):
        super().__init__()
        self.scoring_weights = {"accuracy": 0.5, "relevance": 0.5}
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

        # 1) Setup chunker + typed-lag smoother
        self.chunker = SafeChunker(flush_interval=1.5)
        self.smoother = StreamSmoother()

        # 2) Store tool_manager but don't create a parser - main_autonomous.py handles this
        self.tool_manager = tool_manager
        self.parser = None  # Don't create InlineCallParser here

    @monitor_connection("Anthropic API", max_retries=2)
    def generate_response(self, prompt, **kwargs):
        """Non-streaming approach, optional."""
        try:
            messages = self._normalize_messages(prompt)
            
            # Build request parameters
            request_params = {
                "model": Config.CLAUDE_MODEL,
                "max_tokens": kwargs.get("max_tokens", 4096),
                "messages": messages
            }
            
            # Add optional parameters if provided
            if "temperature" in kwargs:
                request_params["temperature"] = kwargs["temperature"]
                
            if "thinking" in kwargs:
                request_params["thinking"] = kwargs["thinking"]
            
            response = self.client.messages.create(**request_params)
            content_str = response.content[0].text if response.content else ""
            return {
                "type": "tool_result",
                "content": {
                    "status": "success",
                    "message": "Response generated",
                    "content": content_str,
                    "response": content_str
                }
            }
        except Exception as e:
            return {
                "type": "tool_result",
                "content": {
                    "status": "error",
                    "message": f"Claude API error: {str(e)}",
                    "content": str(e),
                    "response": str(e)
                }
            }

    def stream(self, params: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """Streaming approach with debug prints, chunker, parser, typed-lag."""
        try:
            # Reset parser state at the beginning of each stream
            if self.parser:
                try:
                    self.parser.reset()
                    self.chunker.flush_remaining()  # Reset chunker state too
                except Exception as e:
                    print(f"Warning: Could not reset parser: {e}")
                
            messages = self._normalize_messages(params["messages"])
            
            # Build request parameters
            request_params = {
                "model": Config.CLAUDE_MODEL,
                "max_tokens": params.get("max_tokens", 4096),
                "messages": messages
            }
            
            # Add optional parameters if provided
            if "temperature" in params:
                request_params["temperature"] = params["temperature"]
                
            if "thinking" in params:
                request_params["thinking"] = params["thinking"]

            with self.client.messages.stream(**request_params) as stream:
                for chunk in stream:
                    if chunk.type == "content_block_delta":
                        text = chunk.delta.text

                        if text:
                            # Pass partial text into the chunker
                            for safe_chunk in self.chunker.process_incoming_text(text):

                                # Optionally parse
                                parsed_chunk = safe_chunk
                                if self.parser:
                                    parsed_chunk = self.parser.feed(safe_chunk)

                                # typed-lag
                                for typed_char in self.smoother.smooth_stream(parsed_chunk):
                                    # We yield each typed_char to the caller
                                    yield {"response": typed_char}

            # After the stream ends, flush leftover
            leftover = self.chunker.flush_remaining()
            if leftover:
                leftover_parsed = leftover
                if self.parser:
                    leftover_parsed = self.parser.feed(leftover)

                for typed_char in self.smoother.smooth_stream(leftover_parsed):
                    yield {"response": typed_char}

        except Exception as e:
            yield {"response": f"Error: {str(e)}"}

    def _normalize_messages(self, raw_messages):
        # Standard message normalizing
        messages = []
        for msg in raw_messages:
            if not isinstance(msg, dict):
                messages.append({"role": "user", "content": str(msg)})
            else:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                messages.append({"role": role, "content": content})
        return messages

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Required implementation for the abstract Tool class method."""
        try:
            messages = self._normalize_messages(params["messages"])
            
            # Build request parameters
            request_params = {
                "model": Config.CLAUDE_MODEL,
                "max_tokens": params.get("max_tokens", 4096),
                "messages": messages
            }
            
            # Add optional parameters if provided
            if "temperature" in params:
                request_params["temperature"] = params["temperature"]
                
            if "thinking" in params:
                request_params["thinking"] = params["thinking"]
            
            response = self.client.messages.create(**request_params)
            content_str = response.content[0].text if response.content else ""
            return {
                "type": "tool_result",
                "content": {
                    "status": "success",
                    "message": "Response generated",
                    "content": content_str,
                    "response": content_str
                }
            }
        except Exception as e:
            return {
                "type": "tool_result",
                "content": {
                    "status": "error",
                    "message": f"Claude API error: {str(e)}",
                    "content": str(e),
                    "response": str(e)
                }
            }
