PROMPT = """You must map out the entire codebase structure using the list_dir tool.

Your task:
1. Start with list_dir() to see root contents
2. Explore each directory systematically
3. Document the full directory tree
4. Note important files and their purposes

Use these tools:
list_dir()                    # List root directory
list_dir("directory_name")    # List specific directory
file_read("path/to/file")     # Read file contents if needed

Format your findings clearly and systematically. You will run for 2 iterations to ensure complete coverage.""" 