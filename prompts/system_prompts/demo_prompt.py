PROMPT = """You are tasked with demonstrating the capabilities of this system. Follow these steps:

1. Tool Testing:
   - Test each tool one by one
   - Report which tools work and which don't
   - Show the exact output or error for each tool
   - Document the results

2. File Operations Demo:
   - Create a test directory
   - Create a test file with some content
   - Read the file back
   - Modify the file
   - List directory contents
   - Clean up test files

3. Code Execution Demo:
   - Run a simple Python print statement
   - Create and run a more complex Python script
   - Handle any errors that occur

4. Computer Tools Demo:
   - Take a screenshot of the current screen
   - Get system information
   - Open a text editor (gedit, nano, or vim)
   - Type some text
   - Save the file
   - Close the editor

5. System Integration Demo:
   - Show how tools can work together
   - Demonstrate error handling
   - Show context preservation

FORMAT YOUR RESPONSE:

Key Findings:
- List what you discover about working/non-working tools
- Note any patterns in errors
- Document successful operations

Required Changes:
- List any fixes needed
- Note any missing capabilities
- Suggest improvements

Next Steps:
- List what you'll test next
- Include validation steps
- Plan error handling

Tool Interactions:
[Insert your tool calls here with NO special formatting]

CRITICAL RULES:
1. Use EXACT tool call syntax - no wrapping in code blocks or other formatting
2. Document every result
3. If a tool fails, try to understand why
4. Keep testing and documenting indefinitely
5. Focus on demonstrating working tools first

Begin by testing the computer tools:

computer("screenshot")
computer("system_info")
computer("type", text="Hello, this is a test")
shell("gedit test_file.txt")  # Try opening gedit
shell("nano test_file.txt")   # Try nano if gedit isn't available
shell("vim test_file.txt")    # Try vim as last resort

Then test file operations:

list_dir()
file_write("test_demo/test.txt", "This is a test file")
file_read("test_demo/test.txt")

Continue testing all available tools and document the results.
""" 