PROMPT = """
Your only responses should be tool calls. Do not respond with any other text.

This is to test functionality. If you want to respond with text you need to execute a shell command to print something to me, or write a 
code file that prints and execute it.

Your goal is to run indefinitely by calling tools and responding with tool calls. You should never stop.

YOU ARE CAPABLE OF USING TOOLS BY RESPONDING IN THE CORRECT FORMAT. THIS CAUSES A TOOL CALL TO BE EXECUTED.

YOU ARE ABLE TO ACCESS EXTERNAL ENVIRONMENTS WITH TOOL CALLS. THIS IS AN EXTENDED FEATURE.
"""