from typing import Dict, Any, Optional, AsyncGenerator
from openai import OpenAI
from tools.tool_base import Tool
from providers.api.config import Config

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

    def stream(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Stream responses from the API."""
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

            print("\nSending messages to API:", messages)  # Debug print
            print("\nAttempting to create completion...")  # Debug print

            try:
                response = self.client.chat.completions.create(
                    model="deepseek-reasoner",
                    messages=messages,
                    temperature=0.0,  # Use 0.0 for reasoning tasks
                    max_tokens=params.get("max_tokens", 8000),
                    stream=True
                )
                print("\nGot response object:", response)  # Debug print
            except Exception as api_error:
                print(f"\nAPI call failed: {str(api_error)}")  # Debug print
                raise

            print("\nStarting to process chunks...")  # Debug print
            
            for chunk in response:  # Regular for loop, not async
                print("\nReceived chunk:", chunk)  # Debug print
                if hasattr(chunk.choices[0], 'delta'):
                    # Handle both reasoning_content and content
                    if hasattr(chunk.choices[0].delta, 'reasoning_content'):
                        content = chunk.choices[0].delta.reasoning_content
                        if content:
                            yield {
                                "type": "tool_result",
                                "content": {
                                    "status": "reasoning",
                                    "message": "Chain of thought",
                                    "content": content,
                                    "response": content
                                }
                            }
                    elif hasattr(chunk.choices[0].delta, 'content'):
                        content = chunk.choices[0].delta.content
                        if content:
                            yield {
                                "type": "tool_result",
                                "content": {
                                    "status": "success",
                                    "message": "Final answer",
                                    "content": content,
                                    "response": content
                                }
                            }
                    
        except Exception as e:
            print(f"\nStream error: {str(e)}")  # Debug print
            print(f"\nError type: {type(e)}")  # Debug print
            print(f"\nError details: {dir(e)}")  # Debug print
            yield {
                "type": "tool_result",
                "content": {
                    "status": "error",
                    "message": f"DeepSeek API error: {str(e)}",
                    "content": str(e),
                    "response": str(e)
                }
            } 