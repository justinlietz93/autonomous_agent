from typing import Dict, Any, Generator
from openai import OpenAI
from tools.tool_base import Tool
from providers.api.config import Config
from providers.utils.safe_chunker import SafeChunker
from providers.utils.stream_smoother import StreamSmoother
from tools.parse_formatter import InlineCallParser
from tools.tool_manager import ToolManager

class DeepseekR1APIProvider(Tool):
    name = "deepseek-r1_api"
    description = "Provides access to DeepSeek-R1 model via official API"
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
                "default": 8000
            }
        },
        "required": ["messages"]
    }

    def __init__(self, tool_manager: ToolManager = None):
        super().__init__()
        self.client = OpenAI(
            api_key=Config.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"
        )

        # Setup chunker + typed-lag smoother
        self.chunker = SafeChunker(flush_interval=1.5)
        self.smoother = StreamSmoother()

        # If you have a tool_manager, build the parser
        self.tool_manager = tool_manager
        if self.tool_manager:
            self.parser = InlineCallParser(self.tool_manager.tools, marker="TOOL_CALL:")
        else:
            self.parser = None

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Non-streaming approach, optional."""
        try:
            messages = self._normalize_messages(params["messages"])
            response = self.client.chat.completions.create(
                model="deepseek-reasoner",
                messages=messages,
                temperature=params.get("temperature", 0.6),
                max_tokens=params.get("max_tokens", 8000),
                stream=False
            )
            content_str = response.choices[0].message.content if response.choices else ""
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
                    "message": f"DeepSeek API error: {str(e)}",
                    "content": str(e),
                    "response": str(e)
                }
            }

    def stream(self, params: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """Streaming approach with chunker, parser, typed-lag."""
        try:
            messages = self._normalize_messages(params["messages"])
            max_tokens = params.get("max_tokens", 8000)

            stream = self.client.chat.completions.create(
                model="deepseek-reasoner",
                messages=messages,
                temperature=params.get("temperature", 0.6),
                max_tokens=max_tokens,
                stream=True
            )

            for chunk in stream:
                if not chunk or not hasattr(chunk, "choices") or not chunk.choices:
                    continue

                delta_obj = chunk.choices[0].delta
                if not delta_obj:
                    continue

                # Extract content using attribute checks
                content_piece = ""
                if hasattr(delta_obj, "content") and delta_obj.content:
                    content_piece = delta_obj.content
                elif hasattr(delta_obj, "reasoning_content") and delta_obj.reasoning_content:
                    content_piece = delta_obj.reasoning_content

                if content_piece:
                    # Pass partial text into the chunker
                    for safe_chunk in self.chunker.process_incoming_text(content_piece):
                        # Optionally parse
                        parsed_chunk = safe_chunk
                        if self.parser:
                            parsed_chunk = self.parser.feed(safe_chunk)

                        # typed-lag
                        for typed_char in self.smoother.smooth_stream(parsed_chunk):
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
        """Standard message normalizing with strict user/assistant alternation."""
        messages = []
        last_role = None
        
        # Start with system message if not present
        if not raw_messages or raw_messages[0].get("role") != "system":
            messages.append({
                "role": "system",
                "content": "You are an autonomous agent that can use tools to achieve goals."
            })
        
        for msg in raw_messages:
            if not isinstance(msg, dict):
                msg = {"role": "user", "content": str(msg)}
            else:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                msg = {"role": role, "content": content}
            
            # Skip if same role would be repeated
            if last_role == msg["role"]:
                continue
            
            messages.append(msg)
            last_role = msg["role"]
        
        # Ensure we end with a user message
        if messages and messages[-1]["role"] != "user":
            messages.pop()
        
        # Ensure we have at least one message
        if not messages:
            messages.append({"role": "user", "content": "Hello"})
        
        return messages 