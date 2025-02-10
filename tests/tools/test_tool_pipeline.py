import pytest
import logging
import traceback
import sys
from pathlib import Path
from tools.parse_formatter import InlineCallParser
from tools.tool_parser import RealTimeToolParser
from tools.file_tool import FileTool

logger = logging.getLogger(__name__)

@pytest.fixture(autouse=True)
def setup_test_logging(request):
    """Set up logging for this test"""
    logger.info(f"\nPython path: {sys.path}")
    logger.info(f"Current directory: {Path.cwd()}")
    logger.info(f"Test file location: {Path(__file__)}")

def test_complete_tool_pipeline(demo_sandbox):
    """Test the complete pipeline: LLM -> formatter -> parser -> function executor -> smoother -> User"""
    
    logger.info("Starting tool pipeline test")
    
    try:
        # 1. Create tools dictionary (for function executor)
        tools = {
            "file": FileTool().run
        }
        logger.info(f"Created tools dictionary: {tools.keys()}")
        
        # 2. Simulate LLM output (using format from .cursorrules)
        llm_text = f'file_write("{demo_sandbox}/test.txt", "Hello, World!")'
        logger.info(f"LLM output: {llm_text}")
        
        # 3. Format into tool call JSON
        formatter = InlineCallParser(tools, debug=True)
        formatted_call = formatter.feed(llm_text)
        logger.info(f"Formatter output (raw): {repr(formatted_call)}")
        
        # Verify formatter output
        assert len(formatter.rtp.history) == 1, "Exactly one tool call should have been invoked"
        assert formatter.rtp.history[0]["tool"] == "file", "Should have called the 'file' tool"
        assert formatter.rtp.history[0]["input"]["operation"] == "write", "Should have written to file"
        assert formatter.rtp.history[0]["input"]["path"] == str(demo_sandbox / "test.txt"), "Should have written to test.txt"
        assert formatter.rtp.history[0]["input"]["content"] == "Hello, World!", "Should have written the correct content"
        
        # 4. Parse and execute via function executor
        parser = RealTimeToolParser(tools)
        result = parser.feed(formatted_call)
        logger.info(f"Parser/Executor output: {result}")
        
        # 5. Verify execution (simulating smoother -> user)
        test_file = demo_sandbox / "test.txt"
        logger.info(f"Checking file: {test_file}")
        assert test_file.exists(), f"File not created at {test_file}"
        
        content = test_file.read_text()
        logger.info(f"File content: {content}")
        assert content == "Hello, World!"
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        logger.error(f"Exception type: {type(e)}")
        logger.error(traceback.format_exc())
        raise 