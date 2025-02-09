from typing import Dict, Any, Optional, Generator
import anthropic
from tools.tool_base import Tool
from providers.api.config import Config
import asyncio
from queue import Queue
import time
from providers.utils.stream_smoother import StreamSmoother
from providers.utils.throbber import Throbber

class Claude35SonnetProvider(Tool):
    name = "claude-3-5-sonnet_api"
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

    def __init__(self):
        super().__init__()
        self.client = anthropic.Anthropic(
            api_key=Config.ANTHROPIC_API_KEY
        )
        self.smoother = StreamSmoother()

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Format messages for Claude API
            messages = []
            for msg in params["messages"]:
                if not isinstance(msg, dict):
                    msg = {"role": "user", "content": str(msg)}
                elif "role" not in msg:
                    msg = {"role": "user", "content": msg.get("content", str(msg))}
                messages.append(msg)

            response = self.client.messages.create(
                model=Config.CLAUDE_MODEL,
                max_tokens=params.get("max_tokens", 2048),
                messages=messages
            )

            return {
                "type": "tool_result",
                "content": {
                    "status": "success",
                    "message": "Response generated",
                    "content": response.content[0].text,
                    "response": response.content[0].text
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

    def calculate_delay(self, queue_size: int, initial_delay: int = 32, zero_delay_queue_size: int = 64) -> int:
        """Calculate delay based on queue size."""
        return max(0, int(initial_delay - (initial_delay / zero_delay_queue_size) * queue_size))

    def smooth_stream(self, text: str) -> Generator[str, None, None]:
        """Split text into smaller chunks with calculated delays."""
        queue = Queue()
        
        # Split into characters
        for char in text:
            queue.put(char)
            
            # Calculate and apply delay
            delay = self.calculate_delay(queue.qsize())
            if delay > 0:
                time.sleep(delay / 1000)  # Convert to seconds
            
            yield char

    def stream(self, params: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """Stream responses from the API."""
        try:
            # Format messages for Claude API
            messages = []
            for msg in params["messages"]:
                if not isinstance(msg, dict):
                    msg = {"role": "user", "content": str(msg)}
                elif "role" not in msg:
                    msg = {"role": "user", "content": msg.get("content", str(msg))}
                messages.append(msg)

            throbber = Throbber()
            throbber.start()

            try:
                with self.client.messages.stream(
                    model=Config.CLAUDE_MODEL,
                    max_tokens=params.get("max_tokens", 4096),
                    messages=messages
                ) as stream:
                    throbber.stop()

                    for chunk in stream:
                        if chunk.type == "content_block_delta":
                            text = chunk.delta.text
                            if text:
                                for smooth_chunk in self.smoother.smooth_stream(text):
                                    print(smooth_chunk, end="", flush=True)
                                    yield {
                                        "response": smooth_chunk
                                    }

            except Exception as e:
                print(f"\nError: {e}")
                throbber.stop()
                raise

        except Exception as e:
            if 'throbber' in locals():
                throbber.stop()
            yield {
                "response": f"Error: {str(e)}"
            }

