PROMPT = """This is a template for a prompt.

You are to review the codebase of the LLM_kit project. The project includes the following files:
- Provider file: /media/justin/Samsung_4TB1/github/LLM_kit/providers/api/claude-3-5-sonnet-20241022_api_provider.py
- Main entry point: /media/justin/Samsung_4TB1/github/LLM_kit/main_autonomous.py
- Tool call formatter: /media/justin/Samsung_4TB1/github/LLM_kit/tools/parse_formatter.py
- Final parser before tool execution: /media/justin/Samsung_4TB1/github/LLM_kit/tools/tool_parser.py
- All tools: /media/justin/Samsung_4TB1/github/LLM_kit/tools

Your task is to review the entire codebase and document why the file tool is missing on the file_write calls. Analyze the tool call formatter and the final parser, identify any misconfigurations or logic issues, and provide detailed findings with references to the specific code sections involved. Include any recommendations for correcting the issue if applicable.

When you use a tool to read a file or list a directory, you won't be able to see it right away.
The results will be provided to you as context in your next session
"""
