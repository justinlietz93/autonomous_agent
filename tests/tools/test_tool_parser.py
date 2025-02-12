import json
from typing import Dict, Any
import asyncio

# Sample streamed output to test parser
SAMPLE_OUTPUTS = [
    """
<think>
I need to write a test file.
</think>

TOOL_CALL: {
    "tool": "file",
    "input_schema": {
        "operation": "write",
        "path": "parser_test.txt",
        "content": "Test content"
    }
}
""",
    """
Some text before
TOOL_CALL: {
    "tool": "file", 
    "input_schema": {
        "operation": "read",
        "path": "parser_test.txt"
    }
}
Some text after
""",
    # Test case with incorrect format
    """
TOOL__CALL: {
    "tool": "file",
    "input_schema": {
        "operation": "read",
        "path": "test.txt"
    }
}
"""
]

# Expected results for validation
EXPECTED_RESULTS = [
    {
        "tool": "file",
        "input_schema": {
            "operation": "write",
            "path": "parser_test.txt",
            "content": "Test content"
        }
    },
    {
        "tool": "file",
        "input_schema": {
            "operation": "read",
            "path": "parser_test.txt"
        }
    }
]

async def mock_stream() -> str:
    """Mock a streaming response"""
    for output in SAMPLE_OUTPUTS:
        # Simulate streaming by yielding chunks
        for chunk in output.split('\n'):
            yield chunk + '\n'
            await asyncio.sleep(0.1)

async def test_parser():
    """Test the tool parser with streamed output"""
    from tools.archive.tool_parser import parse_tool_calls
    
    print("\n=== Tool Parser Tests ===")
    print("------------------------")
    print("\nProcessing Stream:")
    print("------------------")
    
    found_calls = []
    async for chunk in mock_stream():
        print(f"\nChunk: {chunk!r}")
        tool_calls = parse_tool_calls(chunk)
        if tool_calls:
            print(f"Found tool call in chunk: {json.dumps(tool_calls, indent=2)}")
            found_calls.extend(tool_calls)
    
    print("\n=== Test Results ===")
    print("-------------------")
    
    # Validate results
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Check number of valid tool calls
    if len(found_calls) == len(EXPECTED_RESULTS):
        print("✓ PASS: Found correct number of tool calls")
        tests_passed += 1
    else:
        print(f"✗ FAIL: Expected {len(EXPECTED_RESULTS)} tool calls, found {len(found_calls)}")
    
    # Test 2: Validate tool call contents
    content_matches = all(
        expected == found
        for expected, found in zip(EXPECTED_RESULTS, found_calls)
    )
    if content_matches:
        print("✓ PASS: Tool call contents match expected")
        tests_passed += 1
    else:
        print("✗ FAIL: Tool call contents don't match expected")
        print("\nExpected:", json.dumps(EXPECTED_RESULTS, indent=2))
        print("\nFound:", json.dumps(found_calls, indent=2))
    
    # Test 3: Check invalid tool call was ignored
    invalid_found = any(
        call["tool"] == "file" and call["input_schema"]["path"] == "test.txt"
        for call in found_calls
    )
    if not invalid_found:
        print("✓ PASS: Invalid tool call (TOOL__CALL) was correctly ignored")
        tests_passed += 1
    else:
        print("✗ FAIL: Invalid tool call was incorrectly processed")
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Tests passed: {tests_passed}/{total_tests}")
    if tests_passed == total_tests:
        print("✓ ALL TESTS PASSED")
    else:
        print(f"✗ {total_tests - tests_passed} TESTS FAILED")

if __name__ == "__main__":
    asyncio.run(test_parser()) 