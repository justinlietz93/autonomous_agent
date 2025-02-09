# providers/api/claude-3-5-sonnet-20241022_api_provider.py

from typing import Dict, Any, Generator
import anthropic

from tools.tool_base import Tool
from providers.api.config import Config
from providers.utils.safe_chunker import SafeChunker
from providers.utils.stream_smoother import StreamSmoother

# If you want in-line calls, import your parser
from tools.parse_formatter import InlineCallParser
# And if you have a tool_manager:
from tools.tool_manager import ToolManager


class Claude35SonnetProvider(Tool):
    name = "claude-3-5-sonnet-20241022_api"
    description = "Provides access to Claude 3.5 Sonnet via Anthropic's API"
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
            }
        },
        "required": ["messages"]
    }

    def __init__(self, tool_manager: ToolManager = None):
        super().__init__()
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

        # 1) Setup chunker + typed-lag smoother
        self.chunker = SafeChunker(flush_interval=1.5)
        self.smoother = StreamSmoother()

        # 2) If you have a tool_manager, build the parser
        self.tool_manager = tool_manager
        if self.tool_manager:
            self.parser = InlineCallParser(self.tool_manager.tools, marker="TOOL_CALL:")
        else:
            self.parser = None

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Non-streaming approach, optional."""
        try:
            messages = self._normalize_messages(params["messages"])
            response = self.client.messages.create(
                model=Config.CLAUDE_MODEL,
                max_tokens=params.get("max_tokens", 4096),
                messages=messages
            )
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
            # print("[DEBUG] Entering .stream() in Claude35SonnetProvider")

            messages = self._normalize_messages(params["messages"])
            max_tokens = params.get("max_tokens", 4096)
            # print(f"[DEBUG] messages => {messages}")

            with self.client.messages.stream(
                model=Config.CLAUDE_MODEL,
                max_tokens=max_tokens,
                messages=messages
            ) as stream:
                # print("[DEBUG] Opened stream with Anthropic.")
                for chunk in stream:
                    # print(f"[DEBUG] RAW CHUNK => {chunk}")

                    if chunk.type == "content_block_delta":
                        text = chunk.delta.text
                        # print(f"[DEBUG] chunk.delta.text => {repr(text)}")

                        if text:
                            # Pass partial text into the chunker
                            for safe_chunk in self.chunker.process_incoming_text(text):
                                # print(f"[DEBUG] safe_chunk => {repr(safe_chunk)}")

                                # Optionally parse
                                parsed_chunk = safe_chunk
                                if self.parser:
                                    parsed_chunk = self.parser.feed(safe_chunk)
                                    # print(f"[DEBUG] parsed_chunk => {repr(parsed_chunk)}")

                                # typed-lag
                                for typed_char in self.smoother.smooth_stream(parsed_chunk):
                                    # We yield each typed_char to the caller
                                    yield {"response": typed_char}

            # After the stream ends, flush leftover
            leftover = self.chunker.flush_remaining()
            if leftover:
                # print(f"[DEBUG] leftover => {repr(leftover)}")
                leftover_parsed = leftover
                if self.parser:
                    leftover_parsed = self.parser.feed(leftover)
                    # print(f"[DEBUG] leftover_parsed => {repr(leftover_parsed)}")

                for typed_char in self.smoother.smooth_stream(leftover_parsed):
                    yield {"response": typed_char}

        except Exception as e:
            print(f"[DEBUG] Exception in .stream => {e}")
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
