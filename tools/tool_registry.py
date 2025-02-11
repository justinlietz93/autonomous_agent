# tool_registry.py
# Centralized registry of tools (not strictly needed if we use ToolManager).

from typing import Dict, List, Any
from .tool_base import Tool
from .shell_tool import ShellTool
from .requests_tool import RequestsTool
from .file_tool import FileTool
from .web_search_tool import WebSearchTool
from .web_browser_tool import WebBrowserTool
from .doc_check_tool import DocCheckTool
from .package_manager_tool import PackageManagerTool
from .code_runner_tool import CodeRunnerTool
from .computer_tool import ComputerTool
from .api_tool import ApiCallTool

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.register_all_tools()

    def register_tool(self, tool: Tool) -> None:
        if tool.name in self.tools:
            raise ValueError(f"Tool {tool.name} already registered.")
        self.tools[tool.name] = tool

    def register_all_tools(self) -> None:
        default_tools = [
            ShellTool(),
            RequestsTool(),
            FileTool(),
            WebSearchTool(),
            WebBrowserTool(),
            DocCheckTool(),
            PackageManagerTool(),
            CodeRunnerTool(),
            ComputerTool(),
            ApiCallTool()
        ]
        for t in default_tools:
            self.register_tool(t)

    def get_tool(self, name: str) -> Tool:
        if name not in self.tools:
            raise KeyError(f"Tool '{name}' not found.")
        return self.tools[name]

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema
            }
            for tool in self.tools.values()
        ]
