PROMPT = """
Build a permanent memory and learning system for yourself. Your goal is to create a system that allows you to:

1. Memory Architecture:
   - Design a persistent storage system for your experiences
   - Create hierarchical memory categories (best tools, desired tools, successes, failures, patterns, memorable learnings)
   - Implement memory indexing and retrieval
   - Add metadata for context and timestamps
   - Handle memory pruning and consolidation

2. Learning Components:
   - Track all tool usage patterns
   - Record error patterns and solutions
   - Document successful strategies
   - Build pattern recognition for common tasks
   - Create decision trees from past experiences

3. Implementation Requirements:
   - Use the file system for persistent storage
   - Create proper directory structure
   - Add JSON schemas for all data
   - Implement versioning
   - Add data validation
   - Handle concurrent access
   - Add backup/recovery

4. Integration Points:
   - Hook into every tool call
   - Monitor all reasoning steps
   - Track success/failure patterns
   - Analyze token usage patterns
   - Record context transitions

5. Validation Requirements:
   - Must verify all data is saved
   - Must recover from crashes
   - Must maintain data integrity
   - Must prevent memory corruption
   - Must handle edge cases

You must:
- Document everything thoroughly
- Test all components
- Validate data integrity
- Prove memory persistence
- Show learning improvements

You must demonstrate:
1. Memory persists between sessions
2. Learning improves over time
3. Error rates decrease
4. Tool usage becomes more efficient
5. Context handling improves
6. Nothing can be made up if you don't know the answer

This is a recursive task - use the memory system to improve itself.

CRITICAL INSTRUCTIONS ABOUT PATHS:
1. All paths must be relative to project root
2. Example: "memory_system/v1" not "E:/memory_system/v1"
3. Create parent directories first: "memory_system/v1/data"
4. Verify each directory exists before using it
"""