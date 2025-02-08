# types.py
# Basic typed dict for tool results.

from typing import Dict, Any, Union, TypedDict
from .tool_base import ToolResult as BaseToolResult

class ToolResult(TypedDict):
    type: str
    content: Union[str, Dict[str, Any]]

__all__ = ['ToolResult']
