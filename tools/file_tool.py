# LLM_KIT/tools/file_tool.py

from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, Optional, List, Literal, get_args
from .tool_base import Tool
from .types import ToolResult
import os
import shutil

Command = Literal[
    "view",
    "create", 
    "str_replace",
    "insert",
    "undo_edit",
]

class FileTool(Tool):
    """
    A powerful file system tool that supports both precise edits and bulk operations.
    """

    api_type: Literal["text_editor_20241022"] = "text_editor_20241022"
    name: Literal["file"] = "file"

    def __init__(self):
        self._file_history = defaultdict(list)  # Initialize history
        self.SNIPPET_LINES = 6  # Lines of context around edits
        super().__init__()

    @property
    def description(self) -> str:
        return (
            "A powerful file system tool that supports reading, writing, and editing files.\n"
            "Operations:\n"
            "- write: Create or overwrite a file (creates directories if needed)\n"
            "- read: Read entire file content\n" 
            "- read_lines: Read specific line range\n"
            "- edit_lines: Edit specific line range\n"
            "- append: Append content to existing file\n"
            "- delete: Delete file or directory\n"
            "- mkdir: Create directory\n"
            "- copy: Copy file or directory\n"
            "- move: Move file or directory\n"
            "- list_dir: List directory contents\n"
            "\nAll file operations automatically create parent directories when needed."
        )

    @property 
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": [
                        "read", "read_chunk", "write", "append", 
                        "edit_lines", "read_lines", "delete", 
                        "mkdir", "rmdir", "copy", "move", "list_dir",
                        "undo_edit"
                    ],
                    "description": "The operation to perform"
                },
                "path": {
                    "type": "string", 
                    "description": "Path to the file or directory (parent directories created automatically)"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write (for write/append/edit operations)"
                },
                "start_line": {
                    "type": "integer",
                    "description": "Starting line number for chunk read or edit operations"
                },
                "end_line": {
                    "type": "integer", 
                    "description": "Ending line number for line operations (1-based)"
                },
                "dest": {
                    "type": "string",
                    "description": "Destination path for copy/move operations"
                }
            },
            "required": ["operation", "path"]
        }

    def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the requested file operation."""
        operation = input.get("operation", "")
        path = input.get("path", "")
        
        if not operation or not path:
            return self._error("operation and path are required")

        try:
            # Standardize path handling
            project_root = os.getcwd()
            abs_path = os.path.normpath(os.path.join(project_root, path))
            rel_path = os.path.relpath(abs_path, project_root)
            
            # Create parent dirs for write operations
            if operation in ["write", "append", "copy", "move"]:
                parts = abs_path.split(os.sep)
                current = project_root
                for part in parts[:-1]:
                    current = os.path.join(current, part)
                    os.makedirs(current, exist_ok=True)

            # Handle operations using standardized paths
            if operation == "write":
                content = input.get("content")
                if not content:
                    return self._error("content is required for write operation")
                # Save current content to history if file exists
                if os.path.exists(abs_path):
                    with open(abs_path, 'r', encoding='utf-8') as f:
                        self._file_history[Path(abs_path)].append(f.read())
                with open(abs_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return self._success(f"Successfully wrote to {rel_path}")
                
            elif operation == "read":
                if not os.path.exists(abs_path):
                    return self._error(f"File not found: {rel_path}")
                with open(abs_path) as f:
                    content = f.read()
                return self._success(content)
                
            elif operation == "read_lines":
                start = input.get("start_line")
                end = input.get("end_line")
                if not start or not end:
                    return self._error("start_line and end_line required for read_lines")
                if not os.path.exists(abs_path):
                    return self._error(f"File not found: {rel_path}")
                    
                with open(abs_path) as f:
                    lines = f.readlines()
                if start < 1 or end > len(lines):
                    return self._error(f"Line numbers out of range (1-{len(lines)})")
                    
                result = []
                for i in range(start-1, end):
                    result.append(f"{i+1}: {lines[i].rstrip()}")
                return self._success("\n".join(result))
                
            elif operation == "edit_lines":
                start = input.get("start_line")
                end = input.get("end_line")
                content = input.get("content")
                if not all([start, end, content]):
                    return self._error("start_line, end_line and content required for edit_lines")
                
                # Create file if it doesn't exist
                if not os.path.exists(abs_path):
                    with open(abs_path, 'w', encoding='utf-8') as f:
                        f.write("")
                
                # First count the lines in the file
                with open(abs_path, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for _ in f)
                
                # If edit is within bounds, do a simple edit
                if start <= line_count:
                    with open(abs_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        
                    # Save history before modification
                    self._file_history[Path(abs_path)].append("".join(lines))
                    
                    # Handle the edit
                    new_lines = content.splitlines()
                    lines[start-1:end] = [line + '\n' for line in new_lines]
                    
                    with open(abs_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    
                # If edit is beyond current file size, append empty lines first
                else:
                    with open(abs_path, 'r', encoding='utf-8') as f:
                        current_content = f.read()
                    
                    # Save history before modification
                    self._file_history[Path(abs_path)].append(current_content)
                    
                    # Calculate how many empty lines we need
                    empty_lines_needed = start - line_count - 1
                    
                    # Append the empty lines and the new content
                    with open(abs_path, 'a', encoding='utf-8') as f:
                        # Add empty lines until we reach the target line
                        f.write('\n' * empty_lines_needed)
                        # Add the new content
                        f.write(content + '\n')
                
                return self._success(f"Successfully edited lines {start}-{end} in {rel_path}")
                
            elif operation == "delete":
                if not os.path.exists(abs_path):
                    return self._error(f"Path not found: {rel_path}")
                if os.path.isdir(abs_path):
                    shutil.rmtree(abs_path)
                else:
                    os.remove(abs_path)
                return self._success(f"Successfully deleted {rel_path}")
                
            elif operation == "mkdir":
                os.makedirs(abs_path, exist_ok=True)
                return self._success(f"Created directory: {rel_path}")
                
            elif operation == "copy":
                dest = input.get("dest")
                if not dest:
                    return self._error("dest is required for copy operation")
                dest = os.path.normpath(os.path.join(project_root, dest))
                
                # Need parent dirs for destination too
                dest_parts = dest.split(os.sep)
                dest_current = project_root
                for part in dest_parts[:-1]:
                    dest_current = os.path.join(dest_current, part)
                    os.makedirs(dest_current, exist_ok=True)
                    
                if os.path.isdir(abs_path):
                    shutil.copytree(abs_path, dest)
                else:
                    shutil.copy2(abs_path, dest)
                return self._success(f"Successfully copied {rel_path} to {os.path.relpath(dest, project_root)}")
                
            elif operation == "move":
                dest = input.get("dest")
                if not dest:
                    return self._error("dest is required for move operation")
                dest = os.path.normpath(os.path.join(project_root, dest))
                
                # Need parent dirs for destination too
                dest_parts = dest.split(os.sep)
                dest_current = project_root
                for part in dest_parts[:-1]:
                    dest_current = os.path.join(dest_current, part)
                    os.makedirs(dest_current, exist_ok=True)
                    
                shutil.move(abs_path, dest)
                return self._success(f"Successfully moved {rel_path} to {os.path.relpath(dest, project_root)}")

            elif operation == "append":
                content = input.get("content")
                if not content:
                    return self._error("content is required for append operation")
                # Save current content to history if file exists
                if os.path.exists(abs_path):
                    with open(abs_path, 'r', encoding='utf-8') as f:
                        self._file_history[Path(abs_path)].append(f.read())
                # Need parent dirs for append too
                with open(abs_path, 'a', encoding='utf-8') as f:
                    f.write(content)
                return self._success(f"Successfully appended to {rel_path}")

            elif operation == "list_dir":
                if not os.path.exists(abs_path):
                    return self._error(f"Directory not found: {rel_path}")
                if not os.path.isdir(abs_path):
                    return self._error(f"Path is not a directory: {rel_path}")
                
                recursive = input.get("recursive", False)
                result = []
                
                def list_items(dir_path, prefix=""):
                    for item in os.listdir(dir_path):
                        item_path = os.path.join(dir_path, item)
                        rel_path = os.path.relpath(item_path, abs_path)
                        if os.path.isdir(item_path):
                            result.append(f"DIR  {prefix}{rel_path}")
                            if recursive:
                                list_items(item_path, prefix)
                        else:
                            result.append(f"FILE {prefix}{rel_path}")
                            
                list_items(abs_path)
                return self._success("\n".join(result))
                
            elif operation == "undo_edit":
                if not os.path.exists(abs_path):
                    return self._error(f"File not found: {rel_path}")
                try:
                    result = self._undo_edit(Path(abs_path))
                    return self._success(result)
                except ValueError as e:
                    return self._error(str(e))
                
            else:
                return self._error(f"Unknown operation: {operation}")
                
        except Exception as e:
            return self._error(str(e))
            
    def _success(self, content: str) -> ToolResult:
        return self.format_result("", content)
        
    def _error(self, message: str) -> ToolResult:
        return self.format_error("", message)

    def _str_replace(self, path: Path, old_str: str, new_str: str) -> str:
        """Implement the str_replace command"""
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        occurrences = content.count(old_str)
        if occurrences == 0:
            raise ValueError(f"Text '{old_str}' not found in file")
        if occurrences > 1:
            lines = [i+1 for i, line in enumerate(content.split("\n")) if old_str in line]
            raise ValueError(f"Multiple occurrences of '{old_str}' found in lines {lines}")

        new_content = content.replace(old_str, new_str)
        
        # Save history before making changes
        self._file_history[path].append(content)
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)

        # Create snippet around the edit
        lines = content.split("\n")
        edit_line = content.split(old_str)[0].count("\n")
        start = max(0, edit_line - self.SNIPPET_LINES)
        end = min(len(lines), edit_line + self.SNIPPET_LINES + new_str.count("\n"))
        snippet = "\n".join(new_content.split("\n")[start:end])

        return f"File edited successfully. Snippet of changes:\n{snippet}"

    def _insert(self, path: Path, insert_line: int, new_str: str) -> str:
        """Implement the insert command"""
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if insert_line < 0 or insert_line > len(lines):
            raise ValueError(f"Invalid insert line {insert_line}")

        # Save history
        self._file_history[path].append("".join(lines))

        # Insert the new content
        new_lines = new_str.split("\n")
        lines[insert_line:insert_line] = new_lines

        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        # Create snippet
        start = max(0, insert_line - self.SNIPPET_LINES)
        end = min(len(lines), insert_line + len(new_lines) + self.SNIPPET_LINES)
        snippet = "".join(lines[start:end])

        return f"Text inserted successfully. Snippet of changes:\n{snippet}"

    def _undo_edit(self, path: Path) -> str:
        """Implement the undo_edit command"""
        if not self._file_history[path]:
            raise ValueError(f"No edit history for {path}")

        previous_content = self._file_history[path].pop()
        with open(path, "w", encoding="utf-8") as f:
            f.write(previous_content)

        return f"Successfully reverted last edit to {path}"

    def write(self, path: str, content: str) -> ToolResult:
        """Write content to a file, creating directories if needed."""
        try:
            directory = os.path.dirname(path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            
            # If writing a Python file, preserve triple-quoted strings by writing as-is
            if path.endswith('.py'):
                # No need to modify the content - write it as-is
                # This allows both """ and ''' style quotes to work
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                # For non-Python files, ensure content ends with newline
                if not path.endswith(('.bin', '.exe', '.pyc')):  # Add other binary extensions as needed
                    if not content.endswith('\n'):
                        content += '\n'
                
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            return self.format_result("", f"Successfully wrote to {os.path.abspath(path)}")
        
        except Exception as e:
            return self.format_error("", f"Error writing file: {str(e)}")
