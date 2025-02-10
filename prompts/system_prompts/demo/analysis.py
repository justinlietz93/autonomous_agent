PROMPT = """Add a detailed description of what this codebase does to the codebase_map.md file.

Your task:
1. Read the existing codebase_map.md
2. Analyze key files to understand functionality
3. Add a comprehensive "System Overview" section
4. Document main features and capabilities

Use these tools:
file_read("codebase_map.md")
file_write("codebase_map.md", content)

Focus on:
- Core functionality
- Key components
- How components interact
- System architecture.""" 