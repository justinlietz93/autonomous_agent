# TODO: COMPLETE THIS FILE api_tool.py

import requests
from typing import Dict, Any, Optional
from .tool_base import Tool, ToolResult

class ApiCallTool(Tool):
    """
    Tool for making API calls to external services.
    Use this tool to collect data or information from various APIs.
    Supports GET, POST, PUT, DELETE methods and allows passing custom headers,
    query parameters, and request body data.
    """

    @property
    def name(self) -> str:
        return "api_call"

    @property
    def description(self) -> str:
        return (
            "Makes API calls to specified endpoints. Supports GET, POST, PUT, DELETE methods. "
            "Allows sending custom headers, query parameters, and body data. Returns response content and status."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
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
                    "description": "The API endpoint to call"
                },
                "headers": {
                    "type": "object",
                    "description": "Optional request headers",
                    "additionalProperties": True
                },
                "params": {
                    "type": "object",
                    "description": "Optional query parameters",
                    "additionalProperties": True
                },
                "data": {
                    "type": "object",
                    "description": "Optional request body data",
                    "additionalProperties": True
                },
                "timeout": {
                    "type": "integer",
                    "description": "Request timeout in seconds",
                    "default": 30
                }
            },
            "required": ["method", "url"]
        }

    def run(self, input: Dict[str, Any]) -> ToolResult:
        """
        Execute an API call.
        
        Args:
            input: Dictionary containing:
                method: HTTP method (e.g., "GET", "POST")
                url: The API endpoint to call
                headers: Optional headers for the request
                params: Optional query parameters
                data: Optional request body data
                timeout: Request timeout in seconds (default: 30)
                
        Returns:
            A structured response containing status, headers, and content, or an error message.
        """
        try:
            url = input.get("url")
            if not url:
                return self.format_error("", "Error: URL is required")

            method = input.get("method", "GET").upper()
            if method not in ["GET", "POST", "PUT", "DELETE"]:
                return self.format_error("", f"Error: Unsupported HTTP method: {method}")

            headers = input.get("headers", {})
            params = input.get("params", {})
            data = input.get("data")
            timeout = min(max(1, input.get("timeout", 30)), 60)

            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
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
