PROMPT = """Research the RCoT architecture from https://github.com/justinlietz93/RCoT and add it to codebase_map.md.

Your task:
1. Read the existing codebase_map.md
2. Research the RCoT architecture
3. Add a "Related Research" section
4. Document how this codebase relates to RCoT concepts

Use these tools:
file_read("codebase_map.md")
file_write("codebase_map.md", content)

Include:
- RCoT architecture overview
- Key concepts from the research
- How it relates to this codebase
- Potential future integrations.""" 