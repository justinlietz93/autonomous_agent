PROMPT = """Using the directory structure discovered in the previous prompt, create a markdown file documenting the codebase structure.

Your task:
1. Create a markdown file named codebase_map.md
2. Use the directory structure from previous context
3. Format it as a clean, hierarchical tree
4. Add brief descriptions for key components

Use this tool:
file_write("codebase_map.md", content)

The markdown should be well-formatted with:
- Headers for main sections
- Tree structure using indentation
- Brief descriptions of key components
- Clean, professional formatting.""" 