PROMPT = """You must take the role of a system architect debugging a complex tool execution system.

Current System:
1. deepseek-advice.py is the main entry point
2. Uses DeepseekToolWrapper to manage tool execution
3. Has ExtendedContextManager for state/token tracking
4. Uses ContinuationTool for session management
5. Saves analysis results to timestamped files

Your Task:
1. Read through the test results and error messages
2. Analyze the tool execution flow
3. Check if tools are properly registered and accessible
4. Verify token tracking and session management
5. Identify where the system flow breaks down
6. Suggest specific fixes for the disconnected components

Focus Areas:
- Tool registration and execution flow
- Token tracking accuracy
- Session state persistence
- Component integration points
- Error handling and logging

Use the available tools to:
1. Read relevant files
2. Check system state
3. Analyze error patterns
4. Compare working vs failing components
5. Verify tool accessibility

Remember: This is a complex system where components must work together:
- DeepseekToolWrapper manages tool execution
- ExtendedContextManager tracks state
- ContinuationTool handles session transitions
- SessionManager maintains context between runs

Your goal is to find where these components are disconnected and fix the integration."""
    
   