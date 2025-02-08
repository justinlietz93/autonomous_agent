# deepseek_ollama_provider.py
# Adapter for local Ollama DeepSeek instance.

import ollama
from typing import Dict, Any
from tools.tool_base import Tool

class OllamaDeepSeekProvider(Tool):
    name = "ollama_deepseek"
    description = "Provides access to local Ollama-hosted DeepSeek models"
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
                model="deepseek-r1:14b",
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
