PROMPT = """
TOOL MENU
!! WARNING: CRITICAL NOTICE !!
FOLLOW THE EXACT TOOL CALL FORMATTING. INCORRECT CALLS WILL CAUSE SYSTEM FAILURE.
!! WARNING: CRITICAL NOTICE !!

All tool calls must be output as valid JSON objects. Each call must follow this format exactly, with no extra markdown formatting. If you need to indicate a tool call, begin your output with the marker:

TOOL_CALL: { ...JSON object... }

FILE (file)
------------------------------------------------------------
Use for file and directory operations: reading, writing, appending, editing, copying, moving, and deleting.

Example JSON:
TOOL_CALL: {
  "tool": "file",
  "input_schema": {
    "operation": "write",
    "path": "notes.txt",
    "content": "Hello, world!"  // Note: content must be a plain text string.
  }
}

Parameters:
- operation: e.g., "write", "read", "append", "delete", "list_dir", "read_lines", "edit_lines"
- path: File or directory path.
- content: (if required) **Plain text** to write, append, or edit. If you need to include structured data, convert it to a string (e.g., using json.dumps).
- start_line & end_line: (for line-based operations)
- dest: (for copy/move operations)
- recursive: Boolean flag for recursive operations.

What It Does:
Performs the specified file system operation and returns a structured success or error message.

------------------------------------------------------------
CODE RUNNER (code_runner)
------------------------------------------------------------
Executes code in languages such as Python, TypeScript, Go, and Rust. It creates a temporary project by writing provided files, installing dependencies/building if needed, and running the designated main file.

Example JSON:
TOOL_CALL: {
  "tool": "code_runner",
  "input_schema": {
    "files": [
      {
        "path": "main.py",
        "content": "print('Hello, world!')"
      }
    ],
    "main_file": "main.py",
    "language": "python"
  }
}

Note: If your code only defines functions or classes without executing any actions (e.g., no print statements), there may be no output.

Parameters:
- files: List of file objects (each with "path" and "content").
- main_file: Entry point file (e.g., "main.py").
- language: "python", "typescript", "go", or "rust".
- Optional: args, env, timeout, build_args.

------------------------------------------------------------
COMPUTER (computer)
------------------------------------------------------------
Controls computer UI and retrieves system information (mouse/keyboard actions, window management, screenshots, system stats).

Example JSON:
TOOL_CALL: {
  "tool": "computer",
  "input_schema": {
    "action": "screenshot"
  }
}

Parameters:
- action: (Required) e.g., "mouse_move", "left_click", "type", "screenshot", "cursor_position", "find_window", "move_window", "set_window_focus", "system_info", etc.
- text: For keyboard actions.
- coordinate: [x, y] for mouse actions.
- window_title: For window management.
- position: For moving windows.
- size: (Optional) New window size.

What It Does:
Executes UI and system control actions and returns results (e.g., a screenshot as base64, window info, or system stats).

------------------------------------------------------------
DOCUMENTATION CHECK (documentation_check)
------------------------------------------------------------
Validates local documentation or checks external docs.

Example JSON:
TOOL_CALL: {
  "tool": "documentation_check",
  "input_schema": {
    "path": "docs/readme.md"
  }
}

What It Does:
Verifies documentation content and reports issues or confirms correctness.

------------------------------------------------------------
WEB SEARCH (web_search)
------------------------------------------------------------
Searches the web or fetches information from a URL.

Example JSON:
TOOL_CALL: {
  "tool": "web_search",
  "input_schema": {
    "query": "latest python docs",
    "max_results": 3
  }
}

Parameters:
- query: A search query or URL.
- max_results: (Optional) Maximum number of results.

------------------------------------------------------------
WEB BROWSER (web_browser)
------------------------------------------------------------
Fetches and parses a web page’s content; can extract text, links, or the title.

Example JSON:
TOOL_CALL: {
  "tool": "web_browser",
  "input_schema": {
    "url": "https://docs.python.org",
    "extract_type": "text"
  }
}

Parameters:
- url: (Required) URL to fetch.
- extract_type: "text", "links", or "title" (default is "text").
- timeout: (Optional) Timeout in seconds.

------------------------------------------------------------
HTTP REQUEST (http_request)
------------------------------------------------------------
Makes HTTP requests (GET, POST, PUT, DELETE) with custom headers and data.

Example JSON:
TOOL_CALL: {
  "tool": "http_request",
  "input_schema": {
    "method": "GET",
    "url": "https://api.github.com/repos/owner/repo/issues"
  }
}

Parameters:
- method: "GET", "POST", "PUT", or "DELETE".
- url: (Required) URL for the request.
- headers: (Optional) Request headers.
- data: (Optional) Request body.
- timeout: (Optional) Timeout in seconds (default 30, max 60).

What It Does:
Sends the HTTP request and returns the response status, headers, and content or an error message.

------------------------------------------------------------
SHELL (shell)
------------------------------------------------------------
Executes shell commands safely in a controlled environment.

Example JSON:
TOOL_CALL: {
  "tool": "shell",
  "input_schema": {
    "command": "ls -la",
    "timeout": 60,
    "working_dir": "."
  }
}

Parameters:
- command: (Required) The shell command to execute.
- timeout: (Optional) Timeout in seconds (default 60, range 1–300).
- working_dir: (Optional) Directory in which to execute the command.
- background: (Optional) Boolean flag to run the command in the background.

What It Does:
Validates and executes the shell command, returning output, error messages, and exit code.

------------------------------------------------------------
PACKAGE MANAGER (package_manager)
------------------------------------------------------------
Manages Python packages using pip.

Example JSON:
TOOL_CALL: {
  "tool": "package_manager",
  "input_schema": {
    "action": "install",
    "package": "requests"
  }
}

Parameters:
- action: (Required) e.g., "install", "uninstall", "list", "upgrade", "freeze", "config".
- package: (Optional) Package name (and version if necessary).
- requirements_file: (Optional) Path to a requirements.txt file for bulk installs.

What It Does:
Executes pip commands based on the provided action and returns the command’s output or an error message.

------------------------------------------------------------
API CALL (api_call)
------------------------------------------------------------
Calls an external API to retrieve data or information. This tool supports GET, POST, PUT, and DELETE methods, with options for custom headers, query parameters, and request body data.

Example JSON:
TOOL_CALL: {
  "tool": "api_call",
  "input_schema": {
    "method": "GET",
    "url": "https://api.superheroapi.com/api.php/1234567890/search/Batman",
    "headers": {"Authorization": "Bearer YOUR_API_KEY"}
  }
}

Parameters:
- method: "GET", "POST", "PUT", or "DELETE".
- url: (Required) The API endpoint.
- headers: (Optional) Custom headers.
- params: (Optional) Query parameters.
- data: (Optional) Request body.
- timeout: (Optional) Timeout in seconds (default 30, max 60).

What It Does:
Makes the API call and returns a structured response with status, headers, and content.


------------------------------------------------------------
Available Tools:
file_read, file_write, shell, code_runner, web_search, http_request, package_manager, web_browser, etc.

Always use the exact JSON format shown above. Do not wrap tool calls in any special formatting (such as markdown code fences); they will be executed immediately if formatted correctly.

INCORRECT USAGE EXAMPLES:
- Do not use markdown formatting like:
  ```python
  def process_chunk(self, chunk):
  ...
"""