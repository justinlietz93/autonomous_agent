PROMPT = """You must take the role of a system architect researching DeepSeek's token handling and session management for our tool execution system.

Current System:
- We have a DeepseekToolWrapper that manages tool execution
- ExtendedContextManager handles token tracking and state
- ContinuationTool manages session transitions
- Our token counts (7093) differ from DeepSeek's (4612)
- We're using 1MB chunks vs DeepSeek's recommended sizes
- Session continuations aren't triggering correctly

Key Questions:
1. How does DeepSeek handle token counting and limits?
2. What are the recommended chunk sizes for processing?
3. When should sessions be continued/split?
4. How does DeepSeek handle streaming responses and token tracking?

Research Steps:
1. First use web_browser to access https://api-docs.deepseek.com/
2. Navigate through the documentation structure:
   - Look for sections on token handling
   - Find streaming response documentation
   - Check session management guides
3. Document exact paths and content found
4. Only make conclusions based on actual documentation

For each documentation section:
1. Record the exact URL and section title
2. Quote relevant documentation text
3. Compare with our implementation
4. Note specific discrepancies

Remember to:
- Only use real documentation findings
- Quote exact text from the docs
- Record all documentation URLs
- Note when information isn't found
- Track token usage during research
- Use continue_session if needed for long research

Document Format:
URL: [exact documentation URL]
Section: [section title]
Content: [quoted documentation text]
Relevance: [how it applies to our system]
Discrepancy: [specific differences found]"""