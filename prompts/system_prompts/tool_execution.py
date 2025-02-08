PROMPT = """
Current Issues:
1. Tools are not being called properly
2. Auto-continue functionality isn't triggering
3. Tool responses aren't being processed correctly

Debug Steps Required:
1. Tool Registration Check:
   - Examine tool registration in deepseek-advice.py
   - Verify DeepseekToolWrapper initialization
   - Check tool import paths and availability
   - Validate tool schemas and interfaces

2. Tool Execution Flow:
   - Trace how tool calls are formatted
   - Check how tool responses are processed
   - Verify the wrapper's execute() method
   - Look for any response format mismatches

3. Auto-Continue Analysis:
   - Check ContinuationTool implementation
   - Verify continuation triggers
   - Examine session state handling
   - Debug goal achievement markers

Available Tools:
- file: Read and analyze code files
- shell: Run tests and check output
- doc_check: Review documentation
- code_runner: Test code snippets

Key Files to Examine:
1. deepseek-advice.py:
   - Tool registration
   - Wrapper initialization
   - Auto-continue setup

2. tools/__init__.py:
   - Tool imports
   - Type definitions
   - Base interfaces

3. deepseek_goal_pursuit/tools/continuation_tool.py:
   - Continuation logic
   - Session handling
   - State management

4. tools/tool_base.py:
   - Base tool interface
   - Response formatting
   - Error handling

Debug Process:
1. First, read each file and analyze the code flow
2. Look for disconnects between components
3. Check for format mismatches in tool calls
4. Verify response processing
5. Test each component's functionality
6. Propose specific fixes

Success Criteria:
1. Tools execute properly with correct format
2. Tool responses are processed correctly
3. Auto-continue triggers when needed
4. Session state is maintained properly

Remember:
- Use the file tool to examine code
- Run tests to verify behavior
- Check actual vs expected formats
- Document all findings
- Propose specific fixes

Start by examining the tool registration and execution flow in deepseek-advice.py.
"""