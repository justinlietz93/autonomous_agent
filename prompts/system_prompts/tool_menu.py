"""Tool menu prompt."""

PROMPT = """
Available Tools:
---------------

FILE OPERATIONS
--------------
• file_tool
  - Read, write, and edit files (including code or any other text)
  Examples: 
  file_read("/media/justin/Samsung_4TB/github/LLM_kit/README.md")
  file_write("/media/justin/Samsung_4TB/github/LLM_kit/output.txt", "Hello World")
  file_delete("/media/justin/Samsung_4TB/github/LLM_kit/output.txt")

DOCUMENTATION
------------
• documentation_check
  - Validate and check documentation
  Example: documentation_check("path/to/doc.md")

WEB & SEARCH
-----------
• web_search
  - Search web and extract information
  Example: 
  web_search("python documentation", max_results=5)

• web_browser
  - Fetch and parse web pages
  Example: 
  web_browser("https://docs.python.org", extract_type="text")

• http_request
  - Make HTTP requests
  Example: 
  http_request("GET", "https://api.example.com/data")

DEVELOPMENT
----------
• code_runner
  - Execute code in various languages (python, bash, etc.)
  Example: 
  code_runner("print('hello')", language="python")

• package_manager
  - Manage Python packages with pip
  Example: 
  package_manager("list")
  package_manager("install", "requests")

SYSTEM
------
• shell
  - Execute shell commands
  Example: 
  shell("ls -l")

• computer
  - Control mouse, keyboard, windows
  Example: 
  computer("type", text="Hello World")

SAVE MEMORY
----------
• continue_session
  - Save progress and continue
  Example: 
      save_memory(
      important_discoveries=["Discovery 1", "Discovery 2"],
      completed_tasks=["Task 1"],
      remaining_tasks=["Task 2"],
      notes_for_future_self="This is an important reminder for future self",
      next_step="Start Task 2"
  )

To get detailed schema for any tool, include "show_schema: tool_name" in your reasoning.
""" 