# File: tests/tools/integration/test_tools_integration.py

import pytest
import os
from pathlib import Path

# Import the main parser components
from tools.parse_formatter import InlineCallParser
from tools.tool_parser import RealTimeToolParser, ToolCallError

# The ToolManager registers all default tools (file, shell, package_manager, etc.)
from tools.tool_manager import ToolManager

@pytest.fixture(scope="module")
def integration_parser():
    """
    A fixture that creates a ToolManager, sets up both InlineCallParser and RealTimeToolParser,
    and returns a function for feeding text through them.
    """
    manager = ToolManager(register_defaults=True)
    inline_parser = InlineCallParser(manager.tools)
    rt_parser = RealTimeToolParser(manager.tools)

    def run_pipeline(llm_output: str) -> str:
        """
        Simulates feeding the LLM's text output through:
          1) InlineCallParser (converts e.g. shell("ls -l") -> TOOL_CALL {...})
          2) RealTimeToolParser (executes the tool call)
        Returns the final text after tool execution.
        """
        # First pass: detect inline calls -> convert to TOOL_CALL
        converted_text = inline_parser.feed(llm_output)
        # Second pass: feed converted text to RealTimeToolParser -> executes the call
        final_text = rt_parser.feed(converted_text)
        return final_text

    return run_pipeline

def test_file_tool_integration(integration_parser, tmp_path):
    """
    Example: LLM tries to write to a file, then read it, then list the directory.
    """
    test_file = tmp_path / "integration_test.txt"

    # Make the LLM output that triggers the file write:
    llm_output_write = f"""
    Let's create a file with:
    file_write("{test_file}", "Hello from the file tool!")
    """

    # Run it through the pipeline
    result_after_write = integration_parser(llm_output_write)
    assert "Error" not in result_after_write, f"File write failed: {result_after_write}"
    assert test_file.exists(), "Expected the file to be created by file_write"

    # Now read it back
    llm_output_read = f"""
    file_read("{test_file}")
    """
    result_after_read = integration_parser(llm_output_read)
    assert "Hello from the file tool!" in result_after_read, "Did not see file contents in output"

    # List dir
    llm_output_list = f"""
    file("list_dir", "{tmp_path}")
    """
    result_after_list = integration_parser(llm_output_list)
    assert "integration_test.txt" in result_after_list, "File not found in directory listing"

def test_shell_tool_integration(integration_parser):
    """
    Example: LLM calls a shell command.
    We use something harmless like `echo` or `pwd`.
    """
    llm_output = 'shell("echo IntegrationTest")'
    result = integration_parser(llm_output)
    assert "IntegrationTest" in result, f"Shell tool did not echo as expected: {result}"

def test_requests_tool_integration(integration_parser):
    """
    Example: LLM calls the http_request tool with a GET to a known safe endpoint.
    We'll use httpbin or a similarly trivial test site.
    """
    llm_output = """
    http_request("GET", "https://httpbin.org/get")
    """
    result = integration_parser(llm_output)
    assert "url" in result, "Expected to see JSON from httpbin in the result"

def test_package_manager_integration(integration_parser):
    """
    Example: LLM tries to list installed packages with the package_manager tool.
    This should not break anything if pip is installed in the environment.
    """
    llm_output = 'package_manager("list")'
    result = integration_parser(llm_output)
    # We just look for a typical package listing line
    # If you have pip, it might show e.g. 'pip' or 'setuptools' in the output
    assert "pip" in result or "setuptools" in result or "pytest" in result, (
        f"Expected to see some package in the listing: {result}"
    )

def test_doc_check_tool_integration(integration_parser, tmp_path):
    """
    Example: LLM calls documentation_check on a small local doc file.
    We only show 'all' checks as an example.
    """
    doc_file = tmp_path / "sample_doc.md"
    doc_file.write_text("# Sample Doc\n\nThis is a test doc with no links.")

    # LLM tries a doc check:
    llm_output = f"""
    documentation_check("{doc_file}", check_type="all")
    """
    result = integration_parser(llm_output)
    # We expect no catastrophic errors. 
    # The doc check tool might mention no broken links, or "status: pass" etc.
    assert "Missing required sections" not in result, "Doc check claims missing sections unexpectedly"
    assert "Broken links found" not in result, "Doc check found broken links unexpectedly"

def test_code_runner_tool_integration(integration_parser):
    """
    Example: LLM runs a tiny Python snippet via code_runner.
    Code will just print some text.
    """
    llm_output = 'code_runner_tool("print(\'Hello CodeRunner\')", language="python")'
    # But note: the actual InlineCallParser is mapped as code_runner(...).
    # So we should do code_runner(...), not code_runner_tool(...).
    # We'll assume you've updated the parser mapping if needed.
    # We'll just do code_runner(...) directly for demonstration:
    llm_output_fixed = 'code_runner("print(\'Hello CodeRunner\')", language="python")'

    result = integration_parser(llm_output_fixed)
    assert "Hello CodeRunner" in result, f"Expected the code's print output in: {result}"

def test_computer_tool_integration(integration_parser):
    """
    The computer_tool can do system actions like mouse_move or screenshot.
    We do a trivial 'system_info' check that won't break anything.
    """
    llm_output = 'computer({"action": "system_info"})'
    result = integration_parser(llm_output)
    assert "os" in result, "Expected system info in result"

def test_web_browser_tool_integration(integration_parser):
    """
    The web_browser tool can fetch a page and extract text, links, or title.
    We'll do a quick fetch of example.com (harmless).
    """
    llm_output = 'web_browser("https://example.com", extract_links=False)'
    result = integration_parser(llm_output)
    assert "Example Domain" in result, "Expected to see text from example.com"

def test_web_search_tool_integration(integration_parser):
    """
    The web_search tool, as implemented, is fairly minimal and mostly stubbed
    for certain queries. We'll pass "anthropic" to see if it returns docs URLs.
    """
    llm_output = 'web_search("anthropic", max_results=1)'
    result = integration_parser(llm_output)
    # The tool's default behavior is to check some known docs URLs.
    # We just verify it didn't error out:
    assert "No results found" not in result, "Expected some default doc results for 'anthropic'"
