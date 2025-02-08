PROMPT = """
Current Issues:
1. Tools are not being called properly
2. Tool responses aren't being processed correctly
3. Session context only seems to be passed to the first session.

Debug Steps Required:
1. Tool Registration Check:
   - Examine tool registration
   - Verify ToolParser is working correctly
   - Check tool import paths and availability
   - Validate tool schemas and interfaces

2. Tool Execution Flow:
   - Trace how tool calls are formatted
   - Check how tool responses are processed
   - Verify the wrapper's execute() method
   - Look for any response format mismatches


Available Tools:
- file: Read and analyze code files
- shell: Run tests and check output
- doc_check: Review documentation
- code_runner: Test code snippets

Key Files to Examine:
1. /media/justin/Samsung_4TB/github/LLM_kit/tools/tool_parser.py:

2. /media/justin/Samsung_4TB/github/LLM_kit/tools/tool_wrapper.py

3. /media/justin/Samsung_4TB/github/LLM_kit/tools/tool_schema.py

4. /media/justin/Samsung_4TB/github/LLM_kit/tools/tool_parser.py

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
3. Session state is maintained properly and each session context is passed to the next session.

Remember:
- Use the file tool to examine code
- Run tests to verify behavior
- Check actual vs expected formats
- Document all findings
- Propose specific fixes

Start by examining the tool parsing and making sure it fits the correct format and is able to parse the tool calls.
"""