PROMPT = """
TOOL MENU
!! WARNING: CRITICAL NOTICE !!

IT IS CRUCIAL THAT YOU FOLLOW THE EXACT TOOL CALL FORMATTING. INCORRECT TOOL CALLS WILL CAUSE THE SYSTEM TO FAIL.

!! WARNING: CRITICAL NOTICE !!

FILE (file)
Use for reading, writing, editing, deleting, or managing directories/files. Possible operations include:

read: Read the entire contents of a file.
write: Create or overwrite a file (requires path and content).
append: Append content to an existing file (requires path and content).
delete: Delete a file or directory (requires path).
list_dir: List the contents of a directory (requires path).
read_lines: Read specific lines from a file (requires path, start_line, and end_line).
edit_lines: Replace specific lines in a file (requires path, start_line, end_line, and content).
Examples: file_read("notes.txt") file_write("notes.txt", "New content") file("append", "log.txt", "Additional text") file_delete("oldfile.txt") file("list_dir", "/some/folder", recursive=True) file("read_lines", "script.py", 10, 20) file("edit_lines", "script.py", 15, 18, "Modified code here")

CODE RUNNER (code_runner)
Run code in various languages (Python, TypeScript, Go, Rust). Supports multi-file projects with a main file specification.

Example: code_runner("print('Hello')", language="python")

Supported operations:

files: A list of files to create (each with a "path" and "content").
main_file: The entry point file to execute.
language: The programming language (e.g., "python", "typescript", "go", "rust"). Optional: args, env, timeout, build_args.
COMPUTER (computer)
Interact with the system’s UI, check hardware info, or take screenshots.

Examples: computer("system_info") computer("screenshot")

DOCUMENTATION CHECK (documentation_check)
Validate local documentation or check external docs.

Example: documentation_check("docs/readme.md")

WEB SEARCH (web_search)
Search the web or fetch information from a URL. If using a search query, specify max_results optionally.

Examples: web_search("latest python docs", max_results=3) web_search("https://example.com")

WEB BROWSER (web_browser)
Fetch a webpage and optionally extract text, links, or the title.

Example: web_browser("https://docs.python.org", extract_links=True)

HTTP REQUEST (http_request)
Make HTTP GET/POST/PUT/DELETE requests with optional headers or data.

Example: http_request("GET", "https://api.github.com/repos/owner/repo/issues")

SHELL (shell)
Execute shell commands, with optional timeout or working directory parameters.

Example: shell("ls -al")

PACKAGE MANAGER (package_manager)
Install, list, or uninstall Python packages.

Examples: package_manager("install", "requests") package_manager("list")

SHOW SCHEMA
To see the exact input fields for any tool, include in your reasoning: show_schema: <tool_name>

CONTINUE SESSION
Save progress for future steps with a command like: continue_session( completed_tasks=["Task1"], remaining_tasks=["Task2"], context_summary="Key highlights", next_step="Move on to next tasks" )

Available Tools:

file_read(path): Read the contents of a file.
file_write(path, content): Write content to a file.
shell(command): Execute a shell command.
code_runner(code, language="python"): Run a code snippet.
web_search(query, max_results=5): Search the web.
http_request(method, url): Make an HTTP request.
package_manager(action, package=""): Manage Python packages.
web_browser(url, extract_links=False): Browse a webpage.
Always use the exact format shown in the examples. Do not wrap tool calls in any special formatting. Tool calls will be executed immediately when formatted correctly.


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