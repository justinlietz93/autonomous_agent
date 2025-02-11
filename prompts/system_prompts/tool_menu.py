PROMPT = """
TOOL MENU
!! WARNING: CRITICAL NOTICE !!
FOLLOW THE EXACT TOOL CALL FORMATTING. INCORRECT CALLS WILL CAUSE SYSTEM FAILURE.
!! WARNING: CRITICAL NOTICE !!

------------------------------------------------------------
FILE (file)
------------------------------------------------------------
Use for file/directory operations: reading, writing, appending, editing, copying, moving, deleting.
Example Calls:

file_write("notes.txt", "Hello, world!")

file_read("notes.txt")

Parameters:
– operation: e.g., "write", "read", "append", "delete", "list_dir", "read_lines", "edit_lines"
– path: File or directory path.
– content: (if required) text to write/append/edit.
– start_line & end_line: (for line-based operations)
– dest: (for copy/move operations)
– recursive: Boolean flag for recursive operations.

What It Does:
Performs the specified file system operation and returns a structured success or error message.

------------------------------------------------------------
CODE RUNNER (code_runner)
------------------------------------------------------------
Executes code in languages like Python, TypeScript, Go, and Rust by creating a temporary project, writing provided files, installing dependencies/building if needed, and running the specified main file.
Example Call:

code_runner("print('Hello, world!')", language="python")

Note: If your code only defines functions/classes without executing actions (e.g., no print statements), there will be no output.

Parameters:
– files: List of files (each with "path" and "content")
– main_file: Entry point file (e.g., "main.py")
– language: "python", "typescript", "go", or "rust"
– Optional: args, env, timeout, build_args

------------------------------------------------------------
COMPUTER (computer)
------------------------------------------------------------
Controls computer UI and retrieves system info (mouse/keyboard actions, window management, screenshots, system stats).
Example Call:

computer({"action": "screenshot"})

Parameters:
– action: (Required) e.g., "mouse_move", "left_click", "type", "screenshot", "cursor_position", "find_window", "move_window", "set_window_focus", "system_info", etc.
– text: For keyboard actions.
– coordinate: [x, y] for mouse actions.
– window_title: For window management.
– position: For moving windows.
– size: (Optional) New window size.

What It Does:
Executes UI and system control actions and returns results (e.g., screenshot as base64, window info, or system stats).

------------------------------------------------------------
DOCUMENTATION CHECK (documentation_check)
------------------------------------------------------------
Validates local documentation or checks external docs.
Example Call:

documentation_check("docs/readme.md")

What It Does:
Verifies documentation content and reports issues or confirms correctness.

------------------------------------------------------------
WEB SEARCH (web_search)
------------------------------------------------------------
Searches the web or fetches information from a URL.
Example Calls:

web_search("latest python docs", max_results=3)

web_search("https://google.com")

Parameters:
– query: Search query or URL.
– max_results: (Optional) Maximum number of results.

------------------------------------------------------------
WEB BROWSER (web_browser)
------------------------------------------------------------
Fetches and parses web page content; can extract text, links, or title.
Example Call:

web_browser("https://docs.python.org", extract_type="text")

Parameters:
– url: (Required) URL to fetch.
– extract_type: "text", "links", or "title" (default is "text")
– timeout: (Optional) Timeout in seconds.

------------------------------------------------------------
HTTP REQUEST (http_request)
------------------------------------------------------------
Makes HTTP requests (GET, POST, PUT, DELETE) with custom headers and data.
Example Call:

http_request("GET", "https://api.github.com/repos/owner/repo/issues")

Parameters:
– method: "GET", "POST", "PUT", or "DELETE"
– url: (Required) URL for the request.
– headers: (Optional) Request headers.
– data: (Optional) Request body.
– timeout: (Optional) Timeout (default 30 sec, max 60 sec).

What It Does:
Sends the HTTP request and returns status, headers, and content or error details.

------------------------------------------------------------
SHELL (shell)
------------------------------------------------------------
Executes shell commands safely in a controlled environment.
Example Call:

shell("ls -la")

Parameters:
– command: (Required) Shell command.
– timeout: (Optional) Timeout in seconds (default 60, range 1–300).
– working_dir: (Optional) Directory for command execution.
– background: (Optional) Boolean flag to run in background.
What It Does:
Validates and runs the command, returning output, error messages, and exit code.

------------------------------------------------------------
PACKAGE MANAGER (package_manager)
------------------------------------------------------------
Manages Python packages using pip.
Example Call:

package_manager("install", "requests")

Parameters:
– action: (Required) e.g., "install", "uninstall", "list", "upgrade", "freeze", "config"
– package: (Optional) Package name (and version) for applicable actions.
– requirements_file: (Optional) Path to requirements.txt for bulk installs.
What It Does:
Executes pip commands based on environment options and returns the command’s output or error message.

------------------------------------------------------------
Available Tools:
file_read, file_write, shell, code_runner, web_search, http_request, package_manager, web_browser, etc.

Always use the exact format shown in the examples. Do not wrap tool calls in any special formatting; they will be executed immediately if formatted correctly.

INCORRECT USAGE EXAMPLES:
- Do not use formatting such as:

  ```python
  def process_chunk(self, chunk):
  ...

  ``` bash
  file read --path "memory_best_practices.md"
  ```

  ``` bash
  file read --path "memory_best_practices.md"
  ```

```bash
code_runner --file "tests.py" --command "python -m unittest"
```

```bash
shell --command "ls -l"
```

```json
{
    "action": "List Directory Contents",
    "description": "List the contents of the memory directory.",
    "next_steps": [
        {
            "tool": "list_dir",
            "arguments": "/media/justin/Samsung_4TB1/github/LLM_kit/memory",
            "description": "Explore the memory directory."
        }
    ]
}
```

  
"""