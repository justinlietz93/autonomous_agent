from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, Optional, List, Literal, get_args
from .tool_base import Tool
import os
import shutil

SNIPPET_LINES: int = 10

class FileTool(Tool):
    def __init__(self, sandbox_enabled: bool = False, sandbox_root: str = "/media/justin/Samsung_4TB1/github/LLM_kit/sandbox"):
        """
        A powerful file system tool that supports both precise edits and bulk operations.
        """
        self._file_history = defaultdict(list)
        self.sandbox_enabled = sandbox_enabled
        self.sandbox_root = Path(sandbox_root).resolve()
        super().__init__()


    api_type: Literal["text_editor_20241022"] = "text_editor_20241022"
    name: Literal["file"] = "file"

    @property
    def description(self) -> str:
        return (
            "A powerful file system tool that supports reading, writing, and editing files.\n"
            "Operations:\n"
            "- write: Create or overwrite a file (requires path and content)\n"
            "- read: Read entire file content (requires path; if a directory, list its contents)\n" 
            "- read_lines: Read specific lines (requires path, start_line, end_line)\n"
            "- edit_lines: Edit specific lines (requires path, start_line, end_line, content)\n"
            "- delete: Delete a file or directory (requires path)\n"
            "- mkdir: Create a directory (requires path)\n"
            "- copy: Copy a file or directory (requires path and dest)\n"
            "- move: Move a file or directory (requires path and dest)\n"
            "- append: Append content to a file (requires path and content)\n"
            "- list_dir: List directory contents (requires path)\n"
        )

    @property 
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The operation to perform",
                    "enum": ["write", "read", "read_lines", "edit_lines", "delete", "mkdir", "copy", "move", "append", "list_dir"]
                },
                "path": {
                    "type": "string", 
                    "description": "Path to the file or directory to operate on"
                },
                "content": {
                    "type": ["string", "null"],
                    "description": "Content to write or edit"
                },
                "start_line": {
                    "type": "integer",
                    "description": "Starting line number for line operations (1-based)"
                },
                "end_line": {
                    "type": "integer", 
                    "description": "Ending line number for line operations (1-based)"
                },
                "dest": {
                    "type": "string",
                    "description": "Destination path for copy/move operations"
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Whether to operate recursively on directories"
                }
            },
            "required": ["operation", "path"]
        }
    def _resolve_path(self, path: str, max_depth: int = 3) -> str:
        """
        Resolve a given path to an absolute path.
        
        If sandboxing is enabled (via self.sandbox_enabled and self.sandbox_root), 
        relative paths are resolved relative to the sandbox root, and absolute paths 
        are verified to be within the sandbox.
        
        Otherwise, resolve using the current working directory.
        If the resolved path does not exist, attempt a dynamic search (up to max_depth levels)
        for a directory or file with the same basename.
        """
        from pathlib import Path
        p = Path(path)

        # Check for sandbox option.
        if getattr(self, "sandbox_enabled", False):
            sandbox_root = Path(getattr(self, "sandbox_root", "/tmp/sandbox")).resolve()
            if not p.is_absolute():
                p = sandbox_root / p
            else:
                # If absolute, ensure it is under the sandbox.
                resolved = p.resolve()
                if not str(resolved).startswith(str(sandbox_root)):
                    raise ValueError(f"Access to {path} is not allowed. Must be within sandbox {sandbox_root}")
                p = resolved
            return str(p.resolve())

        # Original logic: if path is absolute, return it.
        if p.is_absolute():
            return str(p)
        
        # Try resolving relative to the current working directory.
        resolved = Path.cwd() / p
        if resolved.exists():
            return str(resolved)
        
        # If not found, perform a dynamic search for a matching basename.
        target_name = p.name
        for root, dirs, files in os.walk(Path.cwd()):
            # Limit the search depth:
            depth = Path(root).relative_to(Path.cwd()).parts
            if len(depth) > max_depth:
                continue
            if target_name in dirs or target_name in files:
                candidate = Path(root) / target_name
                if candidate.exists():
                    return str(candidate.resolve())
        # Fall back to the initially resolved path (which may not exist).
        return str(resolved)


    def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the requested file operation."""
        operation = input.get("operation", "")
        path = input.get("path", "")
        content = input.get("content", "")

        if not operation or not path:
            return {
                "type": "tool_response",
                "tool_use_id": input.get("tool_use_id", ""),
                "content": "Error: operation and path are required"
            }

        # Resolve relative paths
        path = self._resolve_path(path)
        
        try:
            if operation == "write":
                if not content:
                    return self._error("content is required for write operation")
                abs_path = self._resolve_path(path)
                try:
                    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                    with open(abs_path, 'w', encoding="utf-8") as f:
                        f.write(content)
                    return self._success(f"Successfully wrote to {abs_path}")
                except Exception as e:
                    return self._error(f"Failed to write file: {str(e)}")
                
            elif operation == "read":
                if not os.path.exists(path):
                    return self._error(f"File not found: {path}")
                # If the path is a directory, list its contents automatically
                if os.path.isdir(path):
                    try:
                        files = os.listdir(path)
                        return self._success("\n".join(files))
                    except Exception as e:
                        return self._error(f"Error listing directory: {str(e)}")
                with open(path, encoding="utf-8") as f:
                    content = f.read()
                return self._success(content)
                
            elif operation == "read_lines":
                start = input.get("start_line")
                end = input.get("end_line")
                if not start or not end:
                    return self._error("start_line and end_line required for read_lines")
                if not os.path.exists(path):
                    return self._error(f"File not found: {path}")
                    
                with open(path, encoding="utf-8") as f:
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
                if not all([start, end, content]):
                    return self._error("start_line, end_line and content required for edit_lines")
                if not os.path.exists(path):
                    return self._error(f"File not found: {path}")
                    
                with open(path, encoding="utf-8") as f:
                    lines = f.readlines()
                if start < 1 or end > len(lines):
                    return self._error(f"Line numbers out of range (1-{len(lines)})")
                    
                new_lines = content.splitlines()
                lines[start-1:end] = [line + '\n' for line in new_lines]
                
                with open(path, 'w', encoding="utf-8") as f:
                    f.writelines(lines)
                return self._success(f"Successfully edited lines {start}-{end} in {path}")
                
            elif operation == "delete":
                if not os.path.exists(path):
                    return self._error(f"Path not found: {path}")
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                return self._success(f"Successfully deleted {path}")
                
            elif operation == "mkdir":
                recursive = input.get("recursive", False)
                try:
                    os.makedirs(path, exist_ok=True)
                    return self._success(f"Successfully created directory {path}")
                except Exception as e:
                    return self._error(str(e))
                
            elif operation == "copy":
                dest = input.get("dest")
                if not dest:
                    return self._error("dest is required for copy operation")
                dest = self._resolve_path(dest)
                if not os.path.exists(path):
                    return self._error(f"Source not found: {path}")
                    
                if os.path.isdir(path):
                    shutil.copytree(path, dest)
                else:
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    shutil.copy2(path, dest)
                return self._success(f"Successfully copied {path} to {dest}")
                
            elif operation == "move":
                dest = input.get("dest")
                if not dest:
                    return self._error("dest is required for move operation")
                dest = self._resolve_path(dest)
                if not os.path.exists(path):
                    return self._error(f"Source not found: {path}")
                    
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.move(path, dest)
                return self._success(f"Successfully moved {path} to {dest}")

            elif operation == "append":
                if not content:
                    return self._error("content is required for append operation")
                if not os.path.exists(path):
                    return self._error(f"File not found: {path}")
                with open(path, 'a', encoding="utf-8") as f:
                    f.write(content)
                return self._success(f"Successfully appended to {path}")

            elif operation == "list_dir":
                try:
                    if not path or path in [".", "./"]:
                        path = os.getcwd()
                    elif not os.path.isabs(path):
                        path = os.path.join(os.getcwd(), path)
                    
                    if not os.path.exists(path):
                        return {
                            "type": "tool_response",
                            "tool_use_id": "",
                            "content": f"Directory not found: {path}"
                        }
                        
                    files = os.listdir(path)
                    return {
                        "type": "tool_response", 
                        "tool_use_id": "",
                        "content": "\n".join(files)
                    }
                except Exception as e:
                    return self._error(f"Error listing directory: {str(e)}")
                
            else:
                return self._error(f"Unknown operation: {operation}")
                
        except Exception as e:
            return self._error(str(e))
            
    def _success(self, content: str) -> Dict[str, Any]:
        return {
            "type": "tool_response",
            "tool_use_id": "",
            "content": content
        }
        
    def _error(self, message: str) -> Dict[str, Any]:
        return {
            "type": "tool_response", 
            "tool_use_id": "",
            "content": f"Error: {message}"
        }

    def validate_path(self, command: str, path: Path):
        """Check that the path/command combination is valid."""
        if not path.exists() and command != "create":
            raise ValueError(f"The path {path} does not exist")
        if path.exists() and command == "create":
            raise ValueError(f"File already exists at: {path}")
        if path.is_dir() and command != "view":
            raise ValueError(f"The path {path} is a directory and only view command is allowed")

    def _view(self, path: Path, view_range: Optional[List[int]] = None) -> str:
        """Implement the view command"""
        if path.is_dir():
            files = [str(p) for p in path.glob("**/*") if not str(p).startswith(".")]
            return f"Contents of directory {path}:\n" + "\n".join(files)

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if view_range:
            if len(view_range) != 2:
                raise ValueError("view_range must contain exactly 2 integers")
            
            lines = content.split("\n")
            start, end = view_range
            if start < 1 or start > len(lines):
                raise ValueError(f"Invalid start line {start}")
            if end > len(lines):
                raise ValueError(f"Invalid end line {end}")
            if end < start:
                raise ValueError(f"End line {end} cannot be less than start line {start}")
                
            content = "\n".join(lines[start-1:end])

        return f"Contents of {path}:\n{content}"

    def _create(self, path: Path, content: str) -> str:
        """Implement the create command"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File created successfully at: {path}"

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
        start = max(0, edit_line - SNIPPET_LINES)
        end = min(len(lines), edit_line + SNIPPET_LINES + new_str.count("\n"))
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
        start = max(0, insert_line - SNIPPET_LINES)
        end = min(len(lines), insert_line + len(new_lines) + SNIPPET_LINES)
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