PROMPT = """I need you to run some tests on the list directory tool:

YOU ABSOLUTELY MUST USE THE EXACT SYNTAX FOR THE TOOL CALLS!

DO NOT WRAP THEM IN CODE BLOCKS!

list_dir()                          # Lists current directory
list_dir(".")                       # Same as above
list_dir("./")                      # Same as above
list_dir("memory")                  # Lists contents of memory folder
list_dir("memory/context_logs")     # Lists contents of context_logs folder
list_dir("/absolute/path/to/directory")

Please look at the codebase, then create an empty folder, after you've done that begin writing code into it as a demonstration of your ability to use the tool.
"""