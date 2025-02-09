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

CODE RUNNER (code_runner)
-------------------------
- Run code in Python, TypeScript, Go, or Rust (with optional arguments).
Example:
  code_runner("print('Hello')", language="python")

COMPUTER (computer)
-------------------
- Interact with the system’s UI, check hardware info, or take screenshots.
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