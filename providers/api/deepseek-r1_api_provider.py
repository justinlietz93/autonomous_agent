from typing import Dict, Any, Optional
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
            # Ensure messages have role field
            messages = []
            for msg in params["messages"]:
                if not isinstance(msg, dict) or "role" not in msg:
                    # Default to user role if not specified
                    messages.append({"role": "user", "content": str(msg)})
                else:
                    messages.append(msg)

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