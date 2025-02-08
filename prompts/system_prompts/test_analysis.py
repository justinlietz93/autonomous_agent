PROMPT = """This is a codebase for building and testing LLM tools that follow tool use standards.
The core architecture is:

1. Base Tool Class (tool_base.py):
   - All tools inherit from this
   - Defines standard interface for tool use
   - Never modify this file

2. Tool Implementations:
   - Each tool inherits from Tool base class
   - Must work with tool use format
   - Follow strict input/output schemas

3. Test Structure:
   - Unit tests for direct tool functionality
   - Integration tests for LLM interactions
   - System tests for end-to-end flows
   - All tests verify Claude can use tools correctly

4. Key Principles:
   - Claude-first development (tools must work for Claude)
   - Strict adherence to tool schemas
   - Comprehensive test coverage
   - Error handling must be Claude-friendly

I need help fixing some test failures. Here's what I'd like you to do:

1. First, explore the codebase and find relevant test files
2. Read the test results from test_results.txt to understand the failures
3. Find and compare the failing tests with working tests to understand the patterns
4. Analyze what's different between working and failing tests
5. Suggest specific fixes based on the working patterns

You have access to all our tools - based on your own reasoning, feel free to:
- Use the file tools to explore, read and edit files
- Use the doc checker to analyze documentation
- Use the code runner to try out test fixes
- Use the web search and browser tools to check documentation
- Use the computer tool to interact with the system
- Use the package manager to check dependencies
- Use the shell tool to run commands
- Use any other tools that would help analyze the issues

Please explore the codebase yourself to find the relevant files and patterns.

Important Note About Continuations:
When you need to continue in a new session:
1. Use the continue_session tool
2. Provide:
   - completed_tasks: What you've done
   - remaining_tasks: What's left
   - context_summary: Key findings and state
   - next_step: Where to start next
3. The system will handle the transition

Example continuation:
{
    "tool": "continue_session",
    "input_schema": {
        "completed_tasks": ["Read test results", "Analyzed failures"],
        "remaining_tasks": ["Compare with working tests", "Suggest fixes"],
        "context_summary": "Found 8 failing tests, mostly in error handling...",
        "next_step": "Compare failing tests with passing ones in test_requests_llm.py"
    }
}
"""