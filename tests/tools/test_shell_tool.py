import pytest
import logging
import sys
import os
from pathlib import Path
import time
from typing import Dict, Any
from datetime import datetime

from tools.shell_tool import ShellTool
from tests.tools.test_helpers import print_test_step

logger = logging.getLogger(__name__)

@pytest.fixture(scope="class")
def shell_tool():
    """Create ShellTool instance for testing."""
    logger.info("[SETUP] Creating ShellTool instance")
    return ShellTool()

@pytest.fixture(scope="class")
def restricted_shell_tool():
    """Create ShellTool instance with command restrictions."""
    logger.info("[SETUP] Creating restricted ShellTool instance")
    allowed_commands = ["ls", "echo", "pwd", "cat"]
    return ShellTool(allowed_commands=allowed_commands)

@pytest.fixture(scope="class")
def test_dir(request):
    """Create and manage a test directory."""
    test_dir = Path(__file__).parent / "shell_test_dir"
    test_dir.mkdir(exist_ok=True)
    
    # Create a test file
    test_file = test_dir / "test.txt"
    test_file.write_text("Hello, Shell Test!")
    logger.info(f"Created test file: {test_file}")
    
    def cleanup():
        logger.info("\nTest completed - cleaning up test directory...")
        if test_dir.exists():
            for item in test_dir.iterdir():
                item.unlink()
            test_dir.rmdir()
            logger.info("Cleanup complete")

    request.addfinalizer(cleanup)
    return test_dir

class TestShellTool:
    """Test suite for ShellTool."""

    def test_01_basic_command(self, shell_tool):
        """Test basic echo command."""
        logger.info("\n=== Testing Basic Command ===")
        print_test_step("Testing basic echo command")
        
        result = shell_tool.run({
            "command": "echo 'Hello, World!'"
        })
        
        logger.info(f"Command Result: {result}")
        logger.info(f"Content: {result['content']}")
        logger.info(f"Success: {result['success']}")
        
        assert result["type"] == "tool_response"
        assert "Hello, World!" in result["content"]
        assert result["success"] is True

    def test_02_command_with_pipes(self, shell_tool):
        """Test command with pipes."""
        logger.info("\n=== Testing Command with Pipes ===")
        print_test_step("Testing command with pipes")
        
        result = shell_tool.run({
            "command": "echo 'test' | tr 't' 'T'"
        })
        
        logger.info(f"Command Result: {result}")
        logger.info(f"Transformed Content: {result['content']}")
        
        assert result["type"] == "tool_response"
        assert "TesT" in result["content"]
        assert result["success"] is True

    def test_03_working_directory(self, shell_tool, test_dir):
        """Test command execution in specific working directory."""
        logger.info("\n=== Testing Working Directory ===")
        print_test_step("Testing working directory specification")
        
        result = shell_tool.run({
            "command": "pwd",
            "working_dir": str(test_dir)
        })
        
        logger.info(f"Command Result: {result}")
        logger.info(f"Working Directory: {test_dir}")
        
        assert result["type"] == "tool_response"
        assert str(test_dir) in result["content"]
        assert result["success"] is True

    def test_04_timeout_handling(self, shell_tool):
        """Test command timeout."""
        print_test_step("Testing command timeout")
        
        result = shell_tool.run({
            "command": "sleep 2",
            "timeout": 1
        })
        
        assert result["type"] == "tool_response"
        assert "Error: Command timed out" in result["content"]
        assert result["success"] is False

    def test_05_restricted_commands(self, restricted_shell_tool):
        """Test command restrictions."""
        print_test_step("Testing command restrictions")
        
        # Test allowed command
        allowed_result = restricted_shell_tool.run({
            "command": "echo 'test'"
        })
        assert allowed_result["success"] is True
        assert "test" in allowed_result["content"]
        
        # Test disallowed command
        disallowed_result = restricted_shell_tool.run({
            "command": "rm -rf /"
        })
        assert disallowed_result["success"] is False
        assert "not in the allowed list" in disallowed_result["content"]

    def test_06_background_process(self, shell_tool):
        """Test background process execution."""
        print_test_step("Testing background process execution")
        
        result = shell_tool.run({
            "command": "sleep 1 && echo 'done'",
            "background": True
        })
        
        assert result["type"] == "tool_response"
        assert "started in background with PID" in result["content"]
        assert result["success"] is True
        assert "pid" in result

    def test_07_error_handling(self, shell_tool):
        """Test error handling for invalid commands."""
        print_test_step("Testing error handling")
        
        result = shell_tool.run({
            "command": "nonexistentcommand"
        })
        
        assert result["type"] == "tool_response"
        assert "Error" in result["content"]
        assert result["success"] is False
        assert result["exit_code"] != 0

    def test_08_file_operations(self, shell_tool, test_dir):
        """Test file operations through shell commands."""
        print_test_step("Testing file operations through shell")
        
        # Test reading file
        result = shell_tool.run({
            "command": f"cat {test_dir}/test.txt"
        })
        
        assert result["type"] == "tool_response"
        assert "Hello, Shell Test!" in result["content"]
        assert result["success"] is True

    def test_09_environment_variables(self, shell_tool):
        """Test environment variable handling."""
        print_test_step("Testing environment variable handling")
        
        result = shell_tool.run({
            "command": "echo $PATH"
        })
        
        assert result["type"] == "tool_response"
        assert result["content"].strip() != "$PATH"
        assert result["success"] is True

    def test_10_input_validation(self, shell_tool):
        """Test input validation."""
        logger.info("\n=== Testing Input Validation ===")
        print_test_step("Testing input validation")
        
        # Test missing command
        result1 = shell_tool.run({})
        logger.info(f"Missing Command Test Result: {result1}")
        assert result1["type"] == "tool_response"
        assert "Error: Command is required" in result1["content"]
        assert result1["success"] is False
        
        # Test empty command
        result2 = shell_tool.run({"command": ""})
        logger.info(f"Empty Command Test Result: {result2}")
        assert result2["type"] == "tool_response"
        assert "Error" in result2["content"]
        assert result2["success"] is False

def test_shell_tool_llm_integration(shell_tool):
    """Test ShellTool with LLM-style command format."""
    logger.info("\n=== Testing ShellTool LLM Integration ===")
    
    test_cases = [
        ('shell("echo \'Hello from LLM\'")', "Hello from LLM"),
        ('shell("pwd")', str(Path.cwd())),
        ('shell("echo $USER")', os.getenv("USER", "")),
    ]
    
    for llm_command, expected_content in test_cases:
        logger.info(f"\nTesting LLM command: {llm_command}")
        print_test_step(f"Testing LLM command: {llm_command}")
        
        # Extract actual command from LLM format
        import re
        command = re.match(r'shell\("(.+)"\)', llm_command).group(1)
        
        result = shell_tool.run({"command": command})
        logger.info(f"Command Result: {result}")
        logger.info(f"Expected Content: {expected_content}")
        logger.info(f"Actual Content: {result['content']}")
        
        assert result["type"] == "tool_response"
        assert expected_content in result["content"]
        assert result["success"] is True

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 