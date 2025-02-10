# command-r7b:latest_ollama_provider.py
# Adapter for local Ollama command-r7b:latest instance.
#
# This provider supports:
# - Tool integration via tool_manager
# - Streaming with chunking and smoothing
# - Connection validation
# - Error handling

import ollama
import requests
from typing import Dict, Any, Generator, TYPE_CHECKING
from tools.tool_base import Tool
from providers.utils.safe_chunker import SafeChunker
from providers.utils.stream_smoother import StreamSmoother
from tools.parse_formatter import InlineCallParser

if TYPE_CHECKING:
    from tools.tool_manager import ToolManager

class CommandR7bLatestProvider(Tool):
    name = "command-r7b:latest_ollama"
    description = "Provides access to local Ollama-hosted command-r7b:latest models"
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

    def __init__(self, tool_manager: 'ToolManager' = None):
        super().__init__()
        # Add streaming components
        self.chunker = SafeChunker(flush_interval=1.5)
        self.smoother = StreamSmoother()
        
        # Setup tool parsing if tool_manager provided
        self.tool_manager = tool_manager
        if self.tool_manager and hasattr(self.tool_manager, 'tools'):
            print(f"Initializing parser with {len(self.tool_manager.tools)} tools")
            self.parser = InlineCallParser(self.tool_manager.tools, marker="TOOL_CALL:")
        else:
            print("Warning: No tool_manager.tools available - tools will not work")
            self.parser = None
        
        # Check Ollama connection on init
        self._check_ollama_connection()

    def _check_ollama_connection(self) -> bool:
        """Verify Ollama is running and accessible."""
        try:
            # Try to connect to Ollama's default port
            requests.get("http://localhost:11434/api/tags")
            return True
        except requests.exceptions.ConnectionError:
            print("\nERROR: Cannot connect to Ollama. Please ensure Ollama is running:")
            print("1. Install Ollama: curl https://ollama.ai/install.sh | sh")
            print("2. Start Ollama: ollama serve")
            print("3. Pull model: ollama pull command-r7b:latest")
            return False

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            prompt = "\n".join(msg["content"] for msg in params["messages"])
            print("\nStarting Ollama stream...")
            response = ollama.generate(
                model="command-r7b:latest",
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
                "content": full_response  # Match Claude's format
            }
        except Exception as e:
            print(f"Ollama error => {str(e)}")
            return {
                "type": "tool_result",
                "content": f"Ollama connection failed => {str(e)}"
            }

    def stream(self, params: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """Add streaming support matching Claude's interface"""
        if not self._check_ollama_connection():
            yield {"response": "Error: Ollama is not running. Please start Ollama first."}
            return

        try:
            # Debug tool availability
            if self.parser:
                print(f"Tools available: {list(self.parser.TOOL_NAME_MAP.keys())}")
            else:
                print("Warning: No parser initialized - tools will not work")

            prompt = "\n".join(msg["content"] for msg in params["messages"])
            print("\nStarting Ollama stream...")
            
            response = ollama.generate(
                model="command-r7b:latest",
                prompt=prompt,
                stream=True
            )

            for chunk in response:
                text = chunk.get("response", "")
                if text:
                    # Use same chunking/parsing/smoothing as Claude
                    for safe_chunk in self.chunker.process_incoming_text(text):
                        parsed_chunk = safe_chunk
                        if self.parser:
                            try:
                                parsed_chunk = self.parser.feed(safe_chunk)
                            except Exception as e:
                                print(f"Parser error: {str(e)}")
                                parsed_chunk = safe_chunk
                            
                        for typed_char in self.smoother.smooth_stream(parsed_chunk):
                            yield {"response": typed_char}

            # Flush any remaining text
            leftover = self.chunker.flush_remaining()
            if leftover:
                leftover_parsed = leftover
                if self.parser:
                    try:
                        leftover_parsed = self.parser.feed(leftover)
                    except Exception as e:
                        print(f"Parser error on leftover: {str(e)}")
                        leftover_parsed = leftover
                    
                for typed_char in self.smoother.smooth_stream(leftover_parsed):
                    yield {"response": typed_char}

        except Exception as e:
            error_msg = f"Ollama error: {str(e)}"
            if "Connection refused" in str(e):
                error_msg += "\nPlease ensure Ollama is running with: ollama serve"
            print(f"\n{error_msg}")
            yield {"response": error_msg}
