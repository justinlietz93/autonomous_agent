import pytest
import logging
import shutil
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import os
import traceback

from tools.file_tool import FileTool
from tools.tool_wrapper import ToolWrapper
from tools.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)

@pytest.fixture
def tool_registry():
    logger.info("\nInitializing Tool Registry")
    registry = ToolRegistry()
    registry.register_tool(FileTool())  # Use register_tool from actual registry
    return registry

@pytest.fixture
def tool_wrapper(tool_registry):
    logger.info("\nCreating Tool Wrapper")
    return ToolWrapper(tool_registry)

@pytest.fixture
def demo_sandbox(request):
    sandbox = Path(__file__).parent / "test_sandbox"
    sandbox.mkdir(exist_ok=True)
    logger.info(f"Created test sandbox at: {sandbox}")

    def cleanup():
        if sandbox.exists():
            shutil.rmtree(sandbox)
            logger.info("Cleaned up test sandbox")
    request.addfinalizer(cleanup)
    return sandbox

def verify_directory_permissions(directory: Path) -> None:
    """Verify directory exists and has correct permissions"""
    try:
        # Ensure absolute path
        directory = directory.resolve()
        logger.info(f"Checking directory: {directory}")
        
        # Check directory exists
        if not directory.exists():
            logger.error(f"Directory does not exist: {directory}")
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
        
        # Check is directory
        if not directory.is_dir():
            raise ValueError(f"Path exists but is not a directory: {directory}")
            
        # Check permissions
        if not os.access(directory, os.W_OK):
            logger.error(f"Directory not writable: {directory}")
            raise PermissionError(f"Cannot write to directory: {directory}")
            
        logger.info(f"Directory verified: {directory} (writable: {os.access(directory, os.W_OK)})")
        
    except Exception as e:
        logger.error(f"Directory verification failed: {str(e)}")
        raise

def write_log_safely(log_file: Path, content: str) -> None:
    """Helper function to write logs with error handling"""
    try:
        logger.info(f"Attempting to write log file: {log_file}")
        
        # Verify directory
        verify_directory_permissions(log_file.parent)
        
        # Check file status before write
        if log_file.exists():
            logger.info(f"Log file exists: {log_file} (size: {log_file.stat().st_size})")
            if not os.access(log_file, os.W_OK):
                raise PermissionError(f"Cannot write to existing file: {log_file}")
        
        # Write with error handling
        logger.info(f"Writing content (length: {len(content)}) to: {log_file}")
        with open(log_file, 'w') as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
            
        # Verify write
        if not log_file.exists():
            raise IOError(f"File does not exist after write: {log_file}")
        
        size = log_file.stat().st_size
        if size == 0:
            raise IOError(f"File is empty after write: {log_file}")
            
        logger.info(f"Successfully wrote log file: {log_file} (size: {size})")
        
        # Verify content
        written_content = log_file.read_text()
        if written_content != content:
            raise IOError(f"File content verification failed for: {log_file}")
        
    except Exception as e:
        logger.error(f"Failed to write log file {log_file}: {str(e)}")
        raise

@pytest.fixture
def log_directory():
    """Create and verify log directory"""
    log_dir = Path(__file__).parent / "generated_test_logs"
    verify_directory_permissions(log_dir)
    return log_dir

class TestFileToolIntegration:
    """Test file operations from LLM call through to execution"""

    def test_file_write_flow(self, tool_registry, demo_sandbox):
        """Test the complete flow from LLM call to file write operation"""
        logger.info("\n=== Testing File Write Operation ===")
        
        # 1. Start with LLM-style call
        llm_call = f'file_write("{demo_sandbox}/test.txt", "Hello, World!")'
        logger.info(f"LLM Call: {llm_call}")
        
        # Execute and verify as before, but use logger.info instead of writing to separate files
        file_tool = tool_registry.get_tool("file")
        result = file_tool.run({
            "operation": "write",
            "path": str(demo_sandbox / "test.txt"),
            "content": "Hello, World!"
        })
        logger.info(f"Execution Result: {result}")
        
        test_file = demo_sandbox / "test.txt"
        content = test_file.read_text() if test_file.exists() else None
        logger.info(f"File Content: {content}")
        
        assert "Successfully wrote" in result["content"]
        assert test_file.exists()
        assert content == "Hello, World!"

    def test_file_read_flow(self, tool_registry, demo_sandbox):
        """Test the complete flow from LLM call to file read operation"""
        logger.info("\n=== Testing File Read Operation ===")
        
        # 1. Create test file
        test_file = demo_sandbox / "test.txt"
        test_file.write_text("Hello, World!")
        logger.info(f"Created test file: {test_file}")
        
        # 2. Start with LLM-style call
        llm_call = f'file_read("{test_file}")'
        
        # 3. Get tool from registry and execute
        file_tool = tool_registry.get_tool("file")
        result = file_tool.run({
            "operation": "read",
            "path": str(test_file)
        })
        logger.info(f"Execution Result: {result}")
        
        # 4. Assertions
        assert "Hello, World!" in result["content"] 