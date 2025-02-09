import pytest
import logging
import sys
import os
import time
import shutil
from datetime import datetime
from pathlib import Path

from tools.file_tool import FileTool
from tests.tools.test_helpers import print_test_step

logger = logging.getLogger(__name__)

def log_operation(operation, input_data, result, file_state=None):
    logger.debug(f"\n{'='*80}\nOPERATION: {operation}")
    logger.debug(f"INPUT:\n{input_data}")
    logger.debug(f"RESULT:\n{result}")
    if file_state:
        logger.debug(f"FILE STATE:\n{file_state}")
    logger.debug('='*80 + '\n')

@pytest.fixture(scope="class")
def file_tool():
    logger.info("[SETUP] Creating FileTool instance")
    return FileTool()

@pytest.fixture(scope="class")
def demo_sandbox(request):
    # Create a real sandbox directory in tests/tools/test_sandbox
    sandbox = Path(__file__).parent / "test_sandbox"
    sandbox.mkdir(exist_ok=True)
    logger.debug(f"[SETUP] Created sandbox at: {sandbox}")

    def cleanup():
        logger.info("\nTest completed - waiting 5 seconds before cleanup...")
        time.sleep(5)  # Wait 5 seconds before cleanup
        if sandbox.exists():
            logger.info(f"Cleaning up sandbox directory: {sandbox}")
            shutil.rmtree(sandbox)
            logger.info("Cleanup complete")

    request.addfinalizer(cleanup)
    return sandbox

@pytest.mark.usefixtures("file_tool", "demo_sandbox")
class TestFileTool:
    def test_01_create_file(self, file_tool, demo_sandbox):
        test_file = demo_sandbox / "test.txt"
        result = file_tool.run({
            "operation": "write",
            "path": str(test_file),
            "content": "Hello, World!"
        })
        assert "Successfully wrote" in result["content"]
        assert test_file.exists()

    def test_02_read_file(self, file_tool, demo_sandbox):
        test_file = demo_sandbox / "test.txt"
        result = file_tool.run({
            "operation": "read",
            "path": str(test_file)
        })
        assert "Hello, World!" in result["content"]

    def test_03_read_lines(self, file_tool, demo_sandbox):
        test_file = demo_sandbox / "test.txt"
        result = file_tool.run({
            "operation": "read_lines",
            "path": str(test_file),
            "start_line": 1,
            "end_line": 1
        })
        assert "Hello, World!" in result["content"]

    def test_04_append_file(self, file_tool, demo_sandbox):
        test_file = demo_sandbox / "test.txt"
        result = file_tool.run({
            "operation": "append",
            "path": str(test_file),
            "content": "\nAppended text"
        })
        assert "Successfully appended" in result["content"]

    def test_05_copy_file(self, file_tool, demo_sandbox):
        test_file = demo_sandbox / "test.txt"
        copy_path = demo_sandbox / "test_copy.txt"
        result = file_tool.run({
            "operation": "copy",
            "path": str(test_file),
            "dest": str(copy_path)
        })
        assert "Successfully copied" in result["content"]
        assert copy_path.exists()

    def test_06_edit_file(self, file_tool, demo_sandbox):
        test_file = demo_sandbox / "test.txt"
        result = file_tool.run({
            "operation": "edit_lines",
            "path": str(test_file),
            "start_line": 1,
            "end_line": 1,
            "content": "Hello, Modified World!"
        })
        assert "Successfully edited" in result["content"]

    def test_07_create_directory(self, file_tool, demo_sandbox):
        subdir = demo_sandbox / "subdir"
        result = file_tool.run({
            "operation": "mkdir",
            "path": str(subdir)
        })
        assert "Successfully created directory" in result["content"]
        assert subdir.exists()

    def test_08_move_file(self, file_tool, demo_sandbox):
        test_file = demo_sandbox / "test.txt"
        new_path = demo_sandbox / "subdir" / "test.txt"
        result = file_tool.run({
            "operation": "move",
            "path": str(test_file),
            "dest": str(new_path)
        })
        assert "Successfully moved" in result["content"]
        assert not test_file.exists()
        assert new_path.exists()

    def test_09_list_directory(self, file_tool, demo_sandbox):
        result = file_tool.run({
            "operation": "list_dir",
            "path": str(demo_sandbox),
            "recursive": True
        })
        assert "DIR  subdir" in result["content"]
        assert "FILE subdir/test.txt" in result["content"]
        assert "FILE test_copy.txt" in result["content"]

    def test_10_delete_moved_file(self, file_tool, demo_sandbox):
        moved_file = demo_sandbox / "subdir" / "test.txt"
        result = file_tool.run({
            "operation": "delete",
            "path": str(moved_file)
        })
        assert "Successfully deleted" in result["content"]
        assert not moved_file.exists()

    def test_11_delete_copy_file(self, file_tool, demo_sandbox):
        copy_file = demo_sandbox / "test_copy.txt"
        result = file_tool.run({
            "operation": "delete",
            "path": str(copy_file)
        })
        assert "Successfully deleted" in result["content"]
        assert not copy_file.exists()

    def test_12_verify_final_state(self, file_tool, demo_sandbox):
        result = file_tool.run({
            "operation": "list_dir",
            "path": str(demo_sandbox)
        })
        assert "FILE" not in result["content"]
        assert "DIR  subdir" in result["content"]

def test_file_tool_operations(file_tool, demo_sandbox):
    """Test a sequence of file operations with detailed logging."""
    logger.info("STARTING FILE TOOL OPERATIONS TEST")
    print("\nFile Tool Operations Test")
    print("=" * 50)

    try:
        # Display basic environment info
        logger.debug(f"Python: {sys.version}\nWorking Dir: {os.getcwd()}\nSandbox: {demo_sandbox}")

        print("\n1. Basic File Operations")
        print("-" * 30)
        
        # Create test file
        test_file = demo_sandbox / "test.txt"
        create_input = {
            "operation": "write",
            "path": str(test_file),
            "content": "Hello, World!"
        }
        create_result = file_tool.run(create_input)
        log_operation("CREATE FILE", create_input, create_result, 
                      f"File Created: {test_file.exists()}\nSize: {test_file.stat().st_size if test_file.exists() else 0}")
        assert "Successfully wrote" in create_result["content"]
        assert test_file.exists()
        print_test_step("Created file: test.txt")

        # Read operations
        print("\n2. Read Operations")
        print("-" * 30)
        
        read_input = {
            "operation": "read",
            "path": str(test_file)
        }
        read_result = file_tool.run(read_input)
        log_operation("READ FILE", read_input, read_result)
        assert "Hello, World!" in read_result["content"]
        print_test_step("Read file contents successfully")

        # Read lines operation
        read_lines_input = {
            "operation": "read_lines",
            "path": str(test_file),
            "start_line": 1,
            "end_line": 1
        }
        read_lines_result = file_tool.run(read_lines_input)
        log_operation("READ LINES", read_lines_input, read_lines_result)
        assert "Hello, World!" in read_lines_result["content"]
        print_test_step("Read specific lines from file")

        # Append operation
        append_input = {
            "operation": "append",
            "path": str(test_file),
            "content": "\nAppended text"
        }
        append_result = file_tool.run(append_input)
        log_operation("APPEND FILE", append_input, append_result)
        assert "Successfully appended" in append_result["content"]
        print_test_step("Appended content to file")

        # Copy operation
        copy_path = demo_sandbox / "test_copy.txt"
        copy_input = {
            "operation": "copy",
            "path": str(test_file),
            "dest": str(copy_path)
        }
        copy_result = file_tool.run(copy_input)
        log_operation("COPY FILE", copy_input, copy_result,
                     f"Source exists: {test_file.exists()}\nCopy exists: {copy_path.exists()}")
        assert "Successfully copied" in copy_result["content"]
        assert copy_path.exists()
        print_test_step("Created copy of file")

        print("\n3. File Modifications")
        print("-" * 30)
        # Edit operation
        edit_input = {
            "operation": "edit_lines",
            "path": str(test_file),
            "start_line": 1,
            "end_line": 1,
            "content": "Hello, Modified World!"
        }
        edit_result = file_tool.run(edit_input)
        with test_file.open("r") as f:
            content = f.read()
        log_operation("EDIT FILE", edit_input, edit_result, f"Current Content:\n{content}")
        assert "Successfully edited" in edit_result["content"]
        assert "Hello, Modified World!" in content
        print_test_step("Modified file content")

        print("\n4. Directory Operations")
        print("-" * 30)
        # Directory operations
        subdir = demo_sandbox / "subdir"
        mkdir_input = {
            "operation": "mkdir",
            "path": str(subdir)
        }
        mkdir_result = file_tool.run(mkdir_input)
        log_operation("CREATE DIRECTORY", mkdir_input, mkdir_result,
                      f"Directory Created: {subdir.exists()}\nPermissions: {oct(subdir.stat().st_mode)[-3:]}")
        assert "Successfully created directory" in mkdir_result["content"]
        assert subdir.exists()
        print_test_step("Created subdirectory")

        # Move operation
        new_path = subdir / "test.txt"
        move_input = {
            "operation": "move",
            "path": str(test_file),
            "dest": str(new_path)
        }
        move_result = file_tool.run(move_input)
        log_operation("MOVE FILE", move_input, move_result,
                      f"Source exists: {test_file.exists()}\nDest exists: {new_path.exists()}")
        assert "Successfully moved" in move_result["content"]
        assert not test_file.exists()
        assert new_path.exists()
        print_test_step("Moved file to subdirectory")

        # List operation
        list_input = {
            "operation": "list_dir",
            "path": str(demo_sandbox),
            "recursive": True
        }
        list_result = file_tool.run(list_input)
        log_operation("LIST DIRECTORY", list_input, list_result,
                      f"Directory Structure:\n{list_result['content']}")
        assert "DIR  subdir" in list_result["content"]
        assert "FILE subdir/test.txt" in list_result["content"]
        print_test_step("Listed directory contents")

        print("\n5. Cleanup Operations")
        print("-" * 30)
        # Cleanup operations
        delete_input = {
            "operation": "delete",
            "path": str(new_path)
        }
        delete_result = file_tool.run(delete_input)
        log_operation("DELETE FILE", delete_input, delete_result,
                      f"File Exists: {new_path.exists()}")
        assert "Successfully deleted" in delete_result["content"]
        assert not new_path.exists()
        print_test_step("Deleted moved file")

        delete_copy_input = {
            "operation": "delete",
            "path": str(copy_path)
        }
        delete_copy_result = file_tool.run(delete_copy_input)
        log_operation("DELETE COPY FILE", delete_copy_input, delete_copy_result,
                      f"File Exists: {copy_path.exists()}")
        assert "Successfully deleted" in delete_copy_result["content"]
        assert not copy_path.exists()
        print_test_step("Deleted copied file")

        print("\n6. Final Verification")
        print("-" * 30)
        # Final verification
        final_list_input = {
            "operation": "list_dir",
            "path": str(demo_sandbox)
        }
        final_list = file_tool.run(final_list_input)
        log_operation("FINAL DIRECTORY STATE", final_list_input, final_list,
                      f"Final Structure:\n{final_list['content']}")
        assert "FILE" not in final_list["content"]
        assert "DIR  subdir" in final_list["content"]
        print_test_step("Verified final directory state")

    except AssertionError as e:
        print_test_step(f"✗ {str(e)}", passed=False)
        raise
    except Exception as e:
        print_test_step(f"✗ Unexpected error: {str(e)}", passed=False)
        raise

    print("\nTest Summary")
    print("-" * 30)
    print_test_step("✓ All operations completed successfully")
