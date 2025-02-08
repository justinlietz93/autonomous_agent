# LLM_KIT/tools/requests_tool.py

import requests
from typing import Dict, Any, Optional
from .tool_base import Tool, ToolResult

class RequestsTool(Tool):
    """
    Tool for making HTTP requests.
    Follows Anthropic Claude tool use standards.
    """

    def __init__(self, default_headers: Optional[Dict[str, str]] = None):
        """
        Initialize with optional default headers.
        
        Args:
            default_headers: Default headers to include in all requests
        """
        self.default_headers = default_headers or {}

    @property
    def name(self) -> str:
        return "http_request"

    @property
    def description(self) -> str:
        return (
            "Makes HTTP requests to specified URLs. Supports GET, POST, PUT, DELETE methods. "
            "Can send custom headers and data. Returns response content and status."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        """Get the input schema for this tool."""
        return {
            "type": "object",
            "properties": {
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST", "PUT", "DELETE"],
                    "description": "HTTP method to use"
                },
                "url": {
                    "type": "string",
                    "description": "URL to send request to"
                },
                "headers": {
                    "type": "object",
                    "description": "Optional request headers",
                    "additionalProperties": True
                },
                "data": {
                    "type": "object",
                    "description": "Optional request body data",
                    "additionalProperties": True
                }
            },
            "required": ["method", "url"]
        }

    def run(self, input: Dict[str, Any]) -> ToolResult:
        """
        Execute an HTTP request.
        
        Args:
            input: Dictionary containing:
                url: The URL to send the request to
                method: HTTP method (default: "GET")
                headers: Request headers
                data: Request body data
                timeout: Request timeout in seconds (default: 30)
                
        Returns:
            Dictionary containing response data or error message
        """
        try:
            url = input.get("url")
            if not url:
                return self.format_error("", "Error: URL is required")

            method = input.get("method", "GET").upper()
            if method not in ["GET", "POST", "PUT", "DELETE"]:
                return self.format_error("", f"Error: Unsupported HTTP method: {method}")

            headers = {**self.default_headers, **(input.get("headers") or {})}
            data = input.get("data")
            timeout = min(max(1, input.get("timeout", 30)), 60)

            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                timeout=timeout
            )

            response.raise_for_status()
            
            result = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response.text
            }

            return self.format_result("", str(result))

        except requests.RequestException as e:
            return self.format_error("", f"Error: Request failed: {str(e)}")
        except Exception as e:
            return self.format_error("", f"Error: {str(e)}")
