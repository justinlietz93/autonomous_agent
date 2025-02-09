from typing import Dict, Any, Optional, AsyncGenerator, Generator
from openai import OpenAI
from tools.tool_base import Tool
from providers.api.config import Config
from providers.utils.stream_smoother import StreamSmoother
from providers.utils.throbber import Throbber
import sys
import threading
import itertools
import time

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
            "temperature": {
                "type": "number",
                "description": "Sampling temperature",
                "default": 0.6
            },
            "max_tokens": {
                "type": "integer",
                "description": "Maximum tokens to generate",
                "default": 8000
            }
        },
        "required": ["messages"]
    }

    def __init__(self):
        super().__init__()
        self.client = OpenAI(
            api_key=Config.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"
        )
        self.smoother = StreamSmoother()

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Ensure messages have role field and alternate properly
            messages = []
            last_role = None
            
            for msg in params["messages"]:
                if not isinstance(msg, dict):
                    msg = {"role": "user", "content": str(msg)}
                elif "role" not in msg:
                    msg = {"role": "user", "content": msg.get("content", str(msg))}
                
                # Skip if same role would be repeated
                if last_role == msg["role"]:
                    continue
                    
                messages.append(msg)
                last_role = msg["role"]

            # Ensure we start with system and end with user
            if not messages:
                messages = [{"role": "user", "content": "Hello"}]
            elif messages[0]["role"] != "system":
                messages.insert(0, {
                    "role": "system",
                    "content": "You are an autonomous agent that can use tools to achieve goals."
                })
            if messages[-1]["role"] != "user":
                messages.pop()  # Remove last non-user message

            response = self.client.chat.completions.create(
                model="deepseek-reasoner",
                messages=messages,
                temperature=params.get("temperature", 0.6),
                max_tokens=params.get("max_tokens", 8000),
                stream=False
            )
            return {
                "type": "tool_result",
                "content": {
                    "status": "success",
                    "message": "Response generated",
                    "content": response.choices[0].message.content,
                    "response": response.choices[0].message.content
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
        try:
            # Same message formatting as run()
            messages = []
            last_role = None
            
            for msg in params["messages"]:
                if not isinstance(msg, dict):
                    msg = {"role": "user", "content": str(msg)}
                elif "role" not in msg:
                    msg = {"role": "user", "content": msg.get("content", str(msg))}
                
                if last_role == msg["role"]:
                    continue
                    
                messages.append(msg)
                last_role = msg["role"]

            if not messages:
                messages = [{"role": "user", "content": "Hello"}]
            elif messages[0]["role"] != "system":
                messages.insert(0, {
                    "role": "system",
                    "content": "You are an autonomous agent that can use tools to achieve goals."
                })
            if messages[-1]["role"] != "user":
                messages.pop()

            throbber = Throbber()
            throbber.start()

            try:
                stream = self.client.chat.completions.create(
                    model="deepseek-reasoner",
                    messages=messages,
                    temperature=0.0,
                    max_tokens=params.get("max_tokens", 8000),
                    stream=True
                )
                throbber.stop()

                for chunk in stream:
                    # Ensure chunk and choices exist
                    if not chunk or not hasattr(chunk, "choices") or not chunk.choices:
                        continue

                    # Get the delta object
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
                        for smooth_chunk in self.smoother.smooth_stream(content_piece):
                            print(smooth_chunk, end="", flush=True)
                            yield {
                                "response": smooth_chunk
                            }

            except Exception as e:
                print(f"\nDEBUG: Error: {e}")
                throbber.stop()
                raise

        except Exception as e:
            if 'throbber' in locals():
                throbber.stop()
            yield {
                "response": f"Error: {str(e)}"
            } 