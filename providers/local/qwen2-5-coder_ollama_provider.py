# Template for Ollama model providers
# To use:
# 1. Copy this file and rename it (e.g. my_model_provider.py)
# 2. Update the class name and model_name
# 3. Implement _get_model_name()

import ollama
from typing import Dict, Any
from tools.tool_base import Tool

class Qwen25CoderProvider(Tool):
    name = "ollama_qwen2.5-coder"
    description = "Provides access to local Ollama-hosted qwen2.5-coder models"
    input_schema = {
        "type": "object",
        "properties": {
            "messages": {
                "type": "array",
                "items": {"type": "object"},
                "description": "Chat message history"
            }
        },
        "required": ["messages"]
    }

    def __init__(self):
        super().__init__()

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            prompt = "\n".join(msg["content"] for msg in params["messages"])
            print("\nStarting Ollama stream...")
            response = ollama.generate(
                model="qwen2.5-coder",
                prompt=prompt,
                stream=True
            )
            full_response = ""
            for chunk in response:
                text_piece = chunk.get("response", "")
                print(text_piece, end="", flush=True)
                full_response += text_piece
            return {
                "type": "tool_result",
                "content": {
                    "status": "success",
                    "message": "Response generated",
                    "content": full_response
                }
            }
        except Exception as e:
            print(f"Ollama error => {str(e)}")
            return {
                "type": "tool_result",
                "content": {
                    "status": "error",
                    "message": f"Ollama connection failed => {str(e)}"
                }
            }
