PROMPT = """
TOOL MENU
=========

!! WARNING: CRITICAL NOTICE !!

IT IS CRUCIAL THAT YOU FOLLOW THE EXACT TOOL CALL FORMATTING.
INCORRECT TOOL CALLS WILL CAUSE THE SYSTEM TO FAIL.

!! WARNING: CRITICAL NOTICE !!

FILE (file)
-----------
- Use for reading, writing, editing, deleting, or managing directories/files.
Examples (bridging format):
  file_read("notes.txt")
  file_write("notes.txt", "New content")
  file_delete("oldfile.txt")
  file("append", "log.txt", "Additional text")
  file("list_dir", "/some/folder", recursive=True)

CORRECT USAGE:

CODE RUNNER (code_runner)
-------------------------
- Run code in Python, TypeScript, Go, or Rust (with optional arguments).
Example:
  code_runner("print('Hello')", language="python")

COMPUTER (computer)
-------------------
- Interact with the system's UI, check hardware info, or take screenshots.
Examples:
  computer("system_info")
  computer("screenshot")

DOCUMENTATION CHECK (documentation_check)
----------------------------------------
- Validate local docs or check external doc sites.
Example:
  documentation_check("docs/readme.md")

WEB SEARCH (web_search)
-----------------------
- Search or fetch info from a URL.
Examples:
  web_search("latest python docs", max_results=3)
  web_search("https://example.com")

WEB BROWSER (web_browser)
-------------------------
- Fetch a webpage with optional extraction of text, links, or title.
Example:
  web_browser("https://docs.python.org", extract_links=True)

HTTP REQUEST (http_request)
---------------------------
- Make GET/POST/PUT/DELETE requests, optionally including headers/data.
Example:
  http_request("GET", "https://api.example.com/data")

SHELL (shell)
-------------
- Execute shell commands with optional timeout or working directory.
Example:
  shell("ls -al")

PACKAGE MANAGER (package_manager)
---------------------------------
- Install, list, or uninstall Python packages.
Examples:
  package_manager("install", "requests")
  package_manager("list")

SHOW SCHEMA
-----------
- For exact input fields, add: "show_schema: <tool_name>" in your reasoning.


INCORRECT USAGE:

     ```python
     def process_chunk(self, chunk):
         max_token = 1024
         chunks = []
         while len(chunk) > max_token:
             chunks.append(chunk[:max_token])
             chunk = chunk[max_token:]
         chunks.append(chunk)
         return chunks
     ```

    ```bash
     file read --path "memory_best_practices.md"
     ```
     
     ```bash
     code_runner --file "tests.py" --command "python -m unittest"
     ```

     ```bash
     shell --command "ls -l"
     ```
     
     
You have access to the following tools that you can call directly:

Examples of valid tool calls:
file_read("memory/context_logs/context_20250208_023434_autonomous_session_01.txt")  
shell("ls -l memory/context_logs")
code_runner("print('Hello')", language="python")
web_search("latest AI developments", max_results=5)
http_request("GET", "https://api.github.com/repos/owner/repo/issues")
package_manager("list")
web_browser("https://github.com", extract_links=True)

Format your tool calls exactly like the examples above - no special wrapping or formatting.
The tools will be executed when you call them.

Available tools:
- file_read(path): Read contents of a file
- file_write(path, content): Write content to a file
- shell(command): Execute shell command
- code_runner(code, language="python"): Run code snippet
- web_search(query, max_results=5): Search the web
- http_request(method, url): Make HTTP request
- package_manager(action, package=""): Manage packages
- web_browser(url, extract_links=False): Browse webpage

Always use the exact format shown in the examples. Do not wrap tool calls in any special formatting.
Tool calls will be executed immediately when formatted correctly.
"""

# CONTINUE SESSION
# ----------------
# - Save progress for future steps.
# Example:
#   continue_session(
#     completed_tasks=["Task1"],
#     remaining_tasks=["Task2"],
#     context_summary="Key highlights",
#     next_step="Move on to next tasks"
#   )