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
import shlex
import pytest

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
        self.max_buffer = 1024 * 10  # 10KB max buffer size

    def feed(self, chunk: str) -> str:
        """Process a chunk of text and extract any tool calls."""
        self.buffer += chunk
        
        # Don't process until we have a complete line or command
        if not ('\n' in self.buffer or ')' in self.buffer):
            return ""
        
        result = ""
        lines = self.buffer.split('\n')
        
        # Process all complete lines except the last one
        for line in lines[:-1]:
            # Look for function call pattern: name(args)
            match = re.match(r'(\w+)\((.*)\)', line.strip())
            if match:
                tool_name = match.group(1)
                args_str = match.group(2)
                
                # Parse the arguments
                args = self._parse_args(args_str)
                
                # Map the tool name to the correct tool
                tool_map = {
                    "print": "code_runner",
                    "code_runner": "code_runner", 
                    "shell": "shell",
                    "documentation_check": "documentation_check",
                    "file_read": "file",
                    "file_write": "file",
                    "file_delete": "file",
                    "web_search": "web_search",
                    "web_browser": "web_browser",
                    "http_request": "http_request",
                    "package_manager": "package_manager"
                }
                
                mapped_tool = tool_map.get(tool_name, tool_name)
                
                # Transform the args into the correct schema for each tool
                input_schema = {}
                
                if mapped_tool == "code_runner":
                    code = args["positional_args"][0] if args["positional_args"] else ""
                    language = args.get("language", "python")
                    input_schema = {
                        "files": [{"path": "main.py", "content": code}],
                        "main_file": "main.py",
                        "language": language
                    }
                
                elif mapped_tool == "file":
                    if tool_name == "file_write":
                        input_schema = {
                            "operation": "write",
                            "path": args["positional_args"][0],
                            "content": args["positional_args"][1]
                        }
                    elif tool_name == "file_read":
                        input_schema = {
                            "operation": "read",
                            "path": args["positional_args"][0]
                        }
                    elif tool_name == "file_delete":
                        input_schema = {
                            "operation": "delete",
                            "path": args["positional_args"][0]
                        }
                    
                elif mapped_tool == "shell":
                    # Fix: Ensure shell command has proper quote handling
                    command = args["positional_args"][0]
                    # If command starts with a quote but doesn't end with one, add it
                    if (command.startswith("'") and not command.endswith("'")) or \
                       (command.startswith('"') and not command.endswith('"')):
                        command = command + command[0]  # Add matching quote
                    input_schema = {"command": command}
                
                elif mapped_tool == "web_search":
                    query = args["positional_args"][0]
                    max_results = int(args.get("max_results", 5))
                    input_schema = {
                        "query": query,
                        "max_results": max_results
                    }
                
                elif mapped_tool == "web_browser":
                    input_schema = {
                        "url": args["positional_args"][0],
                        "extract_type": "links" if args.get("extract_links") else "text"
                    }
                
                elif mapped_tool == "documentation_check":
                    input_schema = {
                        "path": args["positional_args"][0]
                    }
                
                # Add the tool call to the result
                tool_call = {
                    "tool": mapped_tool,
                    "input_schema": input_schema
                }
                result += f"TOOL_CALL: {json.dumps(tool_call)}\n"
                
        # Keep any incomplete line in the buffer
        self.buffer = lines[-1]
        
        # Prevent buffer from growing too large
        if len(self.buffer) > self.max_buffer:
            self.buffer = self.buffer[-self.max_buffer:]
        
        return result

    def _parse_args(self, args_str: str) -> Dict[str, Any]:
        """
        Parse a string like:
            shell("df -h")
            code_runner("print('Checking system uptime')", language="python")
        into a dict with:
            {
              "positional_args": ["print('Checking system uptime')"],
              "language": "python"
            }
        """
        # We will collect all comma-separated chunks first,
        # then if one has '=', we treat it as named_arg=value.
        # Otherwise, it goes into a list under "positional_args".
        result = {"positional_args": []}
        parts = []
        current = []
        in_quotes = False
        quote_char = None

        for char in args_str:
            if char in ('"', "'"):
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    in_quotes = False
                current.append(char)
            elif char == ',' and not in_quotes:
                parts.append(''.join(current).strip())
                current = []
            else:
                current.append(char)
        if current:
            parts.append(''.join(current).strip())

        # Now parse each part for name=value or just a positional
        for i, part in enumerate(parts):
            # For safety, remove surrounding quotes once at the end
            part_stripped = part.strip()
            if '=' in part_stripped:
                # Named argument
                key, val = part_stripped.split('=', 1)
                key = key.strip()
                # remove the outer quotes if any
                val = val.strip().strip('"\'')
                result[key] = val
            else:
                # Positional argument
                # remove outer quotes if any
                val = part_stripped.strip('"\'')
                result["positional_args"].append(val)

        return result

    def _format_tool_call(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a function name + parsed args into the correct tool + input_schema
        for our system. We'll do custom logic for each recognized tool.
        """
        # 1) Map the function name to an actual tool key
        tool_name_map = {
            "print": "code_runner",
            "code_runner": "code_runner",
            "shell": "shell",
            "documentation_check": "documentation_check",
            "file": "file",
            "computer": "computer",
            "file_read": "file",
            "file_write": "file",
            "file_delete": "file",
            "web_search": "web_search",
            "web_browser": "web_browser",
            "http_request": "http_request",  # If you have an "http_request" key in your tools
            "package_manager": "package_manager"
            # ... add any other mappings needed ...
        }
        base_tool = tool_name_map.get(tool_name, tool_name)

        # The final JSON to return
        tool_call = {
            "tool": base_tool,
            "input_schema": {}
        }

        # convenience
        pos_args = args.get("positional_args", [])

        # 2) Depending on which tool, rearrange the arguments properly
        if base_tool == "file":
            # figure out if it's read/write/delete
            # we can deduce from the original tool name
            if "write" in tool_name:
                operation = "write"
            elif "read" in tool_name:
                operation = "read"
            else:
                operation = "delete"
            path = pos_args[0] if len(pos_args) > 0 else ""
            content = pos_args[1] if len(pos_args) > 1 else ""

            tool_call["input_schema"] = {
                "operation": operation,
                "path": path,
                "content": content
            }

        elif base_tool == "code_runner":
            # For code_runner, we want:
            # "files": [{"path": "main.py", "content": <code>}],
            # "main_file": "main.py",
            # "language": <args["language"] or "python">
            code_str = pos_args[0] if len(pos_args) > 0 else ""
            language = args.get("language", "python")
            tool_call["input_schema"] = {
                "files": [{"path": "main.py", "content": code_str}],
                "main_file": "main.py",
                "language": language
            }

        elif base_tool == "shell":
            # shell("df -h")
            # => {"command": "df -h"}
            command_str = pos_args[0] if len(pos_args) > 0 else ""
            tool_call["input_schema"] = {"command": command_str}

        elif base_tool == "documentation_check":
            # documentation_check("docs.md")
            # => {"path": "docs.md"} or if there's more logic for check_type
            path_str = pos_args[0] if len(pos_args) > 0 else ""
            tool_call["input_schema"] = {"path": path_str}
            # Optionally handle named arguments

        elif base_tool == "web_search":
            # web_search("some query", max_results=3)
            query = pos_args[0] if len(pos_args) > 0 else ""
            max_results = int(args.get("max_results", 5))
            tool_call["input_schema"] = {
                "query": query,
                "max_results": max_results
            }

        elif base_tool == "web_browser":
            # web_browser("https://github.com", extract_links=True)
            url = pos_args[0] if len(pos_args) > 0 else ""
            extract_links = args.get("extract_links", False)
            # or you can store it as "extract_type": "links"
            tool_call["input_schema"] = {
                "url": url,
                "extract_type": "links" if extract_links else "text"
            }

        elif base_tool == "http_request":
            # http_request("GET", "https://api.github.com/repos/.../pulls")
            method = pos_args[0] if len(pos_args) > 0 else "GET"
            url = pos_args[1] if len(pos_args) > 1 else ""
            # you can also pass data, headers, etc.
            tool_call["input_schema"] = {
                "method": method,
                "url": url
            }

        elif base_tool == "package_manager":
            # package_manager("install", "requests")
            action = pos_args[0] if len(pos_args) > 0 else "install"
            package = pos_args[1] if len(pos_args) > 1 else ""
            tool_call["input_schema"] = {
                "action": action,
                "package": package
            }

        else:
            # Default: Just pass all named fields
            tool_call["input_schema"] = args

        return tool_call


# Define test sandbox directory
SANDBOX_DIR = Path("/media/justin/Samsung_4TB/github/LLM_kit/tests/tools/tool_sandbox")

# Create sandbox directory if it doesn't exist
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

# Update sample responses to use sandbox paths
SAMPLE_RESPONSES = [
    """I'll perform a series of system checks and operations.

Now let's check system status:
code_runner("print('Checking system uptime')", language="python")

Writing log entry:
file_write("current_status.md", "Creating current status documentation.")

Writing log entry:
file_write("docs.md", "Creating LLM documentation.")

Reading current status:

file_read("current_status.md")

Validating documentation:
documentation_check("docs.md")

Checking disk space:
shell("df -h")

Writing log entry:
file_write("test_log.txt", "Performed system and environment checks.")
""",

    """Now let's perform some web operations:
web_browser("https://github.com", extract_links=True)

Continuing with system operations:
shell("echo 'Continuing operations'")

Testing installed package:
code_runner("import requests; print('Requests module loaded')", language="python")

Cleanup operations:
file_delete("test_log.txt")

Final research:
web_search("https://github.com", max_results=3)
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

def validate_and_sanitize_input(tool_name, args):
    # New validation logic
    if tool_name == "code_runner":
        if 'code' not in args:
            raise ValueError("Code parameter required")
        args['code'] = args['code'].strip().replace('\n', '\\n')
        
    elif tool_name == "file":
        if 'operation' not in args:
            raise ValueError("Operation parameter required")
        if args['operation'] == 'write' and 'content' not in args:
            raise ValueError("Content parameter required for write operations")
            
    elif tool_name == "shell":
        if 'command' not in args:
            raise ValueError("Command parameter required")
        args['command'] = shlex.quote(args['command'])
    
    elif tool_name == "documentation_check":
        if 'path' not in args:
            if 'input' in args:
                args['path'] = args['input']
            else:
                raise ValueError("Path parameter required")
        # Validate path exists
        if not Path(args['path']).exists():
            raise ValueError(f"Documentation path not found: {args['path']}")
    
    return args

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
            "documentation_check": DocCheckTool(docs_root=str(SANDBOX_DIR)),
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