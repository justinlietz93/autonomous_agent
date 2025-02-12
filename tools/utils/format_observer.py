# TODO: COMPLETE THIS FILE tool_observer.py

import re
import logging

# --- Utility: Levenshtein Distance ---
def levenshtein_distance(s1: str, s2: str) -> int:
    """Compute the Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


# --- Observer Class ---
class ToolCallObserver:
    """
    An observer agent that attempts to automatically correct erroneous tool calls.
    
    It uses fuzzy matching to correct the tool name based on a list of valid tools.
    Future improvements could incorporate LLM-based inference for more advanced corrections.
    """
    def __init__(self, valid_tools=None, correction_threshold: int = 3, use_llm: bool = False):
        """
        :param valid_tools: List of valid tool names. If None, a default list is used.
        :param correction_threshold: Maximum allowable Levenshtein distance to consider a correction.
        :param use_llm: Whether to delegate correction to an LLM (stubbed for future scaling).
        """
        if valid_tools is None:
            self.valid_tools = [
                "file_write", "file_read", "shell", "code_runner", "web_search",
                "http_request", "package_manager", "web_browser", "documentation_check", "memory"
            ]
        else:
            self.valid_tools = valid_tools

        self.correction_threshold = correction_threshold
        self.use_llm = use_llm

    def infer(self, raw_input: str, context: str = "") -> str:
        """
        Attempt to infer a corrected tool call from raw_input using heuristic rules.
        
        :param raw_input: The original (possibly erroneous) tool call.
        :param context: Additional context (e.g., error messages) for future inference.
        :return: Corrected input if a likely correction is found; otherwise, returns raw_input.
        """
        if self.use_llm:
            corrected = self._infer_with_llm(raw_input, context)
            if corrected:
                return corrected

        # Fallback: Use fuzzy matching for the tool name.
        return self._fuzzy_correct_tool_name(raw_input)

    def _fuzzy_correct_tool_name(self, raw_input: str) -> str:
        """
        Extract the tool call name and use fuzzy matching to correct it.
        If a correction within the threshold is found, substitute it in the raw input.
        """
        # Look for a function-like pattern, e.g., file_writ("...")
        match = re.search(r'(\w+)\s*\(', raw_input)
        if not match:
            return raw_input  # No tool call detected.

        tool_candidate = match.group(1)
        best_match = tool_candidate
        best_distance = float('inf')

        for valid in self.valid_tools:
            distance = levenshtein_distance(tool_candidate.lower(), valid.lower())
            if distance < best_distance:
                best_distance = distance
                best_match = valid

        if best_distance <= self.correction_threshold and best_match != tool_candidate:
            # Replace only the first occurrence.
            corrected_input = re.sub(r'\b' + re.escape(tool_candidate) + r'\b', best_match, raw_input, count=1)
            logging.debug("Fuzzy correction: '%s' -> '%s' (distance %d)", tool_candidate, best_match, best_distance)
            return corrected_input

        return raw_input

    def _infer_with_llm(self, raw_input: str, context: str) -> str:
        """
        Stub for future LLM-based inference to correct tool calls.
        Currently not implemented.
        """
        # TODO: call an external API here.
        return None


# --- Observer-Integrated Handler ---
def robust_tool_call_handler(raw_input: str, inline_parser, observer: ToolCallObserver) -> str:
    """
    Processes a tool call using the inline_parser.
    If an error occurs, the observer attempts to infer a corrected tool call,
    and the corrected call is re-submitted to the parser.
    
    :param raw_input: The original tool call input.
    :param inline_parser: Your existing inline parser instance.
    :param observer: An instance of ToolCallObserver.
    :return: The output from the parser, either from the original or the corrected call.
    """
    try:
        result = inline_parser.feed(raw_input)
        return result
    except Exception as err:
        logging.error("Initial tool call processing failed: %s", err)
        corrected_input = observer.infer(raw_input, context=str(err))
        if corrected_input and corrected_input != raw_input:
            logging.info("Corrected tool call: %s", corrected_input)
            try:
                result = inline_parser.feed(corrected_input)
                return result
            except Exception as err2:
                logging.error("Retry with corrected tool call failed: %s", err2)
                return f"[Error processing tool call even after correction: {err2}]"
        else:
            return f"[Error: Unable to infer a corrected tool call for: {raw_input}]"


# --- Example Usage ---
if __name__ == "__main__":
    # Configure basic logging for debugging.
    logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] %(levelname)s: %(message)s')
    
    # Assume inline_parser is your existing InlineCallParser instance (from your tool_parser module).
    # For demonstration purposes, we'll use a dummy parser that simply raises an error if "file_write" is misspelled.
    class DummyInlineParser:
        def feed(self, input_str: str) -> str:
            # Simulate a failure if the tool name isn't exactly "file_write"
            if "file_write(" not in input_str:
                raise Exception("Unrecognized tool call format.")
            return "Dummy tool result"

    # Create a dummy parser instance.
    dummy_parser = DummyInlineParser()
    
    # Create the observer with default settings.
    observer = ToolCallObserver(correction_threshold=2)

    # Example erroneous tool call (misspelled "file_write" as "file_writ")
    erroneous_call = 'file_writ("notes.txt", "Hello, observer!")'
    
    output = robust_tool_call_handler(erroneous_call, dummy_parser, observer)
    print("Final output:", output)
