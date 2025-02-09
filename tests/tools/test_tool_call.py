#!/usr/bin/env python3
"""Test script to simulate LLM streaming and tool execution."""


# In order for this test to pass the system needs to read tool calls like these:
    
# web_search("latest advancements in AI", max_results=5)  
# code_runner("print('Checking system uptime')", language="python")  
# http_request("GET", "https://api.github.com/repos/justin/Samsung_4TB/github/LLM_kit/pulls")  
# package_manager("list")  
# file_read("/media/justin/Samsung_4TB/github/LLM_kit/current_status.md")  
# documentation_check("/media/justin/Samsung_4TB/github/LLM_kit/docs.md")  
# shell("df -h")  
# computer("type", text="System check complete")  
# file_write("/media/justin/Samsung_4TB/github/LLM_kit/log.txt", "Performed system and environment checks.")  
# web_browser("https://github.com/justin/Samsung_4TB/github/LLM_kit/issues", extract_links=True)  
# shell("echo 'Continuing operations'")  
# package_manager("install", "requests")  
# code_runner("import requests; print('Requests module loaded')", language="python")  
# http_request("GET", "https://api.github.com/repos/justin/Samsung_4TB/github/status")  
# file_delete("/media/justin/Samsung_4TB/github/LLM_kit/temp_file.txt")  
# shell("top -b -n1 | head -5")  
# web_search("efficient file management techniques", max_results=3)  
# code_runner("print('End of current session actions')", language="python")

# and turn them into structured JSON tool calls to feed to the function executor like this

# TOOL_CALL: {
#     "tool": "file_tool",
#     "input_schema": {
#         "operation": "read",
#         "path": "README.md"
#     }
# }


# TOOL_CALL: {
#     "tool": "file_tool", 
#     "input_schema": {
#         "operation": "write",
#         "path": "test_output.txt",
#         "content": "This is a test file created by the tool parser test."
#     }
# }


# TOOL_CALL: {
#     "tool": "file_tool",
#     "input_schema": {
#         "operation": "read",
#         "path": "test_output.txt"
#     }
# }

import sys
import os
from pathlib import Path
import asyncio
import json
from typing import Dict, Any, AsyncGenerator
from datetime import datetime
import re

# Add project root to path
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root))

# Now import tools after path is set
from tools.code_runner_tool import CodeRunnerTool
from tools.doc_check_tool import DocCheckTool
from tools.shell_tool import ShellTool
from tools.web_browser_tool import WebBrowserTool
from tools.web_search_tool import WebSearchTool
from tools.file_tool import FileTool
from tools.tool_manager import ToolManager
from tools.tool_parser import RealTimeToolParser, ToolCallError
from providers.provider_library import ProviderLibrary

class ToolCallError(Exception):
    """Error raised when tool call parsing fails."""
    def __init__(self, message: str, context: str = None):
        self.message = message
        self.context = context or ""
        super().__init__(self.message)

class RealTimeToolParser:
    def __init__(self, tools):
        self.tools = tools
        self.buffer = ""
        self.in_tool_call = False
        
    def feed(self, chunk: str) -> str:
        """Feed a chunk of text to the parser and return any tool results."""
        self.buffer += chunk
        result = ""
        
        # Look for tool calls in the format: tool_name("arg1", arg2=value)
        while True:
            # Try to find a complete tool call
            tool_call_match = re.search(r'(\w+)\((.*?)\)', self.buffer)
            if not tool_call_match:
                break
                
            tool_name = tool_call_match.group(1)
            args_str = tool_call_match.group(2)
            
            try:
                # Log the original LLM format
                llm_format = f"{tool_name}({args_str})"
                result += f"\nLLM FORMAT: {llm_format}\n"
                
                # Parse the arguments
                args_dict = self._parse_args(args_str)
                
                # Convert to proper tool call format based on tool type
                tool_call = self._format_tool_call(tool_name, args_dict)
                
                # Format as valid JSON string
                tool_call_json = json.dumps(tool_call)
                
                # Add the formatted tool call
                result += f"TOOL_CALL: {tool_call_json}\n"
                
                # Remove the processed tool call from buffer
                self.buffer = self.buffer[tool_call_match.end():]
                
            except Exception as e:
                raise ToolCallError(f"Error parsing tool call: {e}", context=llm_format)
                
        return result

    def _format_tool_call(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Format the tool call based on the tool type."""
        # Map tool names to their actual registered names
        tool_name_map = {
            "file_read": "file",
            "file_write": "file", 
            "file_delete": "file",
            "web_search": "web_search",
            "web_browser": "web_browser",
            "code_runner": "code_runner",
            "shell": "shell",
            "documentation_check": "documentation_check"
        }

        tool_call = {
            "tool": tool_name_map.get(tool_name, tool_name),  # Use mapped name or original
            "input_schema": {}
        }
        
        # Handle file operations
        if tool_name == "file_read":
            tool_call["input_schema"] = {
                "operation": "read",
                "path": args["input"]
            }
        elif tool_name == "file_write":
            # Split on first comma that's not inside quotes
            parts = []
            current = ""
            in_quotes = False
            quote_char = None
            
            for char in args["input"]:
                if char in '"\'':
                    if not in_quotes:
                        in_quotes = True
                        quote_char = char
                    elif char == quote_char:
                        in_quotes = False
                elif char == ',' and not in_quotes:
                    parts.append(current)
                    current = ""
                    continue
                current += char
            
            if current:
                parts.append(current)
                
            if len(parts) == 2:
                tool_call["input_schema"] = {
                    "operation": "write",
                    "path": parts[0].strip().strip('"\''),
                    "content": parts[1].strip().strip('"\'')
                }
            else:
                tool_call["input_schema"] = {
                    "operation": "write",
                    "path": args["input"],
                    "content": args.get("content", "")
                }
        elif tool_name == "file_delete":
            tool_call["input_schema"] = {
                "operation": "delete",
                "path": args["input"]
            }
        # Handle shell commands
        elif tool_name == "shell":
            tool_call["input_schema"] = {
                "command": args["input"]
            }
        # Handle code runner
        elif tool_name == "code_runner":
            tool_call["input_schema"] = {
                "code": args["input"],
                "language": args.get("language", "python")
            }
        # Handle web operations
        elif tool_name == "web_search":
            tool_call["input_schema"] = {
                "query": args["input"],
                "max_results": int(args.get("max_results", 5))
            }
        elif tool_name == "web_browser":
            tool_call["input_schema"] = {
                "url": args["input"],
                "extract_links": args.get("extract_links", False)
            }
        # Default case - pass args directly
        else:
            tool_call["input_schema"] = args
            
        return tool_call

    def _parse_args(self, args_str: str) -> Dict[str, Any]:
        """Parse tool call arguments into a dictionary."""
        # Remove quotes from string arguments
        args_str = re.sub(r'"([^"]*)"', r'\1', args_str)
        args_str = re.sub(r"'([^']*)'", r'\1', args_str)
        
        # Split on commas not inside function calls
        args_parts = []
        current = ""
        paren_count = 0
        
        for char in args_str:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            elif char == ',' and paren_count == 0:
                args_parts.append(current.strip())
                current = ""
                continue
            current += char
            
        if current:
            args_parts.append(current.strip())
            
        # Convert to dictionary
        args_dict = {}
        for part in args_parts:
            if '=' in part:
                key, value = part.split('=', 1)
                args_dict[key.strip()] = value.strip()
            else:
                args_dict['input'] = part.strip()
                
        return args_dict

# Define test sandbox directory
SANDBOX_DIR = Path("/media/justin/Samsung_4TB/github/LLM_kit/tests/tools/tool_sandbox")

# Create sandbox directory if it doesn't exist
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

# Update sample responses to use sandbox paths
SAMPLE_RESPONSES = [
    """I'll perform a series of system checks and operations.

First, let me search for relevant information:
web_search("latest advancements in AI", max_results=5)

Now let's check system status:
code_runner("print('Checking system uptime')", language="python")

Reading current status:
file_read("/media/justin/Samsung_4TB/github/LLM_kit/tests/tools/tool_sandbox/current_status.md")

Validating documentation:
documentation_check("/media/justin/Samsung_4TB/github/LLM_kit/tests/tools/tool_sandbox/docs.md")

Checking disk space:
shell("df -h")

Writing log entry:
file_write("/media/justin/Samsung_4TB/github/LLM_kit/tests/tools/tool_sandbox/log.txt", "Performed system and environment checks.")
""",

    """Now let's perform some web operations:
web_browser("https://github.com/justin/Samsung_4TB/github/LLM_kit/issues", extract_links=True)

Continuing with system operations:
shell("echo 'Continuing operations'")

Testing installed package:
code_runner("import requests; print('Requests module loaded')", language="python")

Cleanup operations:
file_delete("/media/justin/Samsung_4TB/github/LLM_kit/tests/tools/tool_sandbox/temp_file.txt")

Final research:
web_search("efficient file management techniques", max_results=3)
"""
]

def mock_llm_stream(response: str):
    """Simulate an LLM streaming response."""
    # Split into lines to simulate more realistic streaming
    lines = response.split('\n')
    
    for line in lines:
        # Stream larger chunks for faster testing
        for i in range(0, len(line), 10):  # Increased chunk size
            yield line[i:i+10]
        yield '\n'

class TestLogger:
    def __init__(self, test_name: str):
        """Initialize test logger with test name."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_dir = Path(__file__).parent / "generated_test_logs"
        log_dir.mkdir(exist_ok=True)
        
        self.log_file = log_dir / f"{test_name}_{timestamp}.txt"
        self.terminal = sys.stdout
        
    def write(self, message: str):
        """Write to both terminal and log file."""
        self.terminal.write(message)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(message)
            
    def flush(self):
        """Required for file-like objects."""
        self.terminal.flush()

def cleanup_sandbox():
    """Clean up all files in the sandbox directory."""
    if SANDBOX_DIR.exists():
        for item in SANDBOX_DIR.iterdir():
            try:
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    import shutil
                    shutil.rmtree(item)
            except Exception as e:
                print(f"Warning: Could not remove {item}: {e}")

def test_tool_execution():
    """Test the tool parser with real tool execution."""
    logger = TestLogger("tool_execution_test")
    sys.stdout = logger
    
    try:
        print(f"\n=== Tool Execution Test ===")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Sandbox directory: {SANDBOX_DIR}")
        print("-------------------------")
        
        # Initialize tools with explicit registration
        tools = {
            "web_search": WebSearchTool(),
            "code_runner": CodeRunnerTool(),
            "file": FileTool(),  # Note: file_read/write/delete use this
            "documentation_check": DocCheckTool(),
            "shell": ShellTool(),
            "web_browser": WebBrowserTool()
        }
        
        tool_manager = ToolManager(tools)
        parser = RealTimeToolParser(tools=tool_manager.tools)
        
        for i, response in enumerate(SAMPLE_RESPONSES, 1):
            print(f"\nTesting Response {i}:")
            print("-" * 40)
            
            full_response = ""
            tool_results = []
            
            try:
                for chunk in mock_llm_stream(response):
                    print(f"Chunk: {chunk!r}")
                    
                    try:
                        result = parser.feed(chunk)
                        
                        if "TOOL_CALL:" in result:
                            # Extract the tool call JSON - get everything after TOOL_CALL: up to the next newline
                            tool_call_str = result.split("TOOL_CALL: ")[1].split("\n")[0].strip()
                            tool_call = json.loads(tool_call_str)
                            
                            # Get the tool name
                            tool_name = tool_call["tool"]
                            
                            # Execute the tool
                            if tool_name in tool_manager.tools:
                                try:
                                    tool_result = tool_manager.tools[tool_name].run(tool_call["input_schema"])
                                    tool_results.append({
                                        "tool": tool_name,
                                        "input": tool_call["input_schema"],
                                        "result": tool_result
                                    })
                                    result += f"EXECUTION RESULT: {json.dumps(tool_result)}\n"
                                except Exception as e:
                                    result += f"EXECUTION ERROR: {str(e)}\n"
                            else:
                                result += f"TOOL NOT FOUND: {tool_name}\n"
                        
                        full_response += result
                        
                    except ToolCallError as e:
                        print(f"\n[TOOL ERROR: {e}]\n")
                
                print("\nFinal accumulated response:")
                print("-" * 40)
                print(full_response)
                
                print("\nTool Execution Summary:")
                print("-" * 40)
                if tool_results:
                    for idx, result in enumerate(tool_results, 1):
                        print(f"{idx}. {result['tool']}:")
                        print(f"   Input: {json.dumps(result['input'], indent=2)}")
                        print(f"   Result: {json.dumps(result['result'], indent=2)}")
                        print()
                else:
                    print("No tools were executed.")
                    print("Available tools:", list(tool_manager.tools.keys()))
                
            except Exception as e:
                print(f"Error processing response {i}: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    finally:
        # Restore stdout and clean up
        sys.stdout = logger.terminal
        cleanup_sandbox()

def main():
    """Run the tool execution test."""
    try:
        test_tool_execution()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    main() 