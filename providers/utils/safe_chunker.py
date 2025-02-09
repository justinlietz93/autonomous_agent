# providers/utils/safe_chunker.py

import time
from typing import Optional

class SafeChunker:
    """
    SafeChunker handles incremental text as it streams in,
    ensuring it never splits parentheses or curly braces in half.
    Also supports time-based partial flush if no boundary is found.
    """

    def __init__(self, flush_interval: float = 1.5):
        """
        :param flush_interval: number of seconds to wait before
                               forcibly flushing partial buffer
        """
        self.partial_buffer = ""
        self.paren_depth = 0
        self.brace_depth = 0
        self.state = "outside"
        self.flush_interval = flush_interval
        self.last_flush_time = time.time()

    def process_incoming_text(self, new_text: str):
        # print(f"[DEBUG] SafeChunker.process_incoming_text => new_text = {repr(new_text)}")
        self.partial_buffer += new_text

        while True:
            boundary_idx = self.find_smart_boundary(self.partial_buffer)
            if boundary_idx == -1:
                # No boundary found, check if time-based flush
                now = time.time()
                time_since_last_flush = now - self.last_flush_time
                if self.partial_buffer and time_since_last_flush >= self.flush_interval:
                    # forcibly flush
                    forced_chunk = self._flush_all()
                    # print(f"[DEBUG] SafeChunker => TIME-BASED FLUSH => {repr(forced_chunk)}")
                    yield forced_chunk
                break
            else:
                # Found a boundary
                safe_chunk = self.partial_buffer[:boundary_idx + 1]
                self.partial_buffer = self.partial_buffer[boundary_idx + 1:]
                # print(f"[DEBUG] SafeChunker => NORMAL BOUNDARY CHUNK => {repr(safe_chunk)}")
                yield self._flush_chunk(safe_chunk)

    def find_smart_boundary(self, buffer: str) -> int:
        boundary_chars = set(" \t\r\n,.;:!?")
        local_paren_depth = self.paren_depth
        local_brace_depth = self.brace_depth
        local_state = self.state

        for i, ch in enumerate(buffer):
            # Update depth counters
            if ch == '(':
                local_paren_depth += 1
                local_state = "in_paren"
            elif ch == ')':
                local_paren_depth -= 1
                if local_paren_depth < 0:
                    local_paren_depth = 0
                if local_paren_depth == 0 and local_brace_depth == 0:
                    local_state = "outside"
            elif ch == '{':
                local_brace_depth += 1
                local_state = "in_brace"
            elif ch == '}':
                local_brace_depth -= 1
                if local_brace_depth < 0:
                    local_brace_depth = 0
                if local_brace_depth == 0 and local_paren_depth == 0:
                    local_state = "outside"

            # If fully outside, see if char is a boundary
            if local_state == "outside" and local_paren_depth == 0 and local_brace_depth == 0:
                if ch in boundary_chars:
                    return i

        return -1

    def _flush_chunk(self, chunk: str) -> str:
        """Flush a chunk normally at a boundary."""
        self._update_depth_counters(chunk)
        self.last_flush_time = time.time()
        return chunk

    def _flush_all(self) -> str:
        """Forcibly flush everything in partial_buffer."""
        leftover = self.partial_buffer
        self.partial_buffer = ""
        self._update_depth_counters(leftover)
        self.last_flush_time = time.time()
        return leftover

    def _update_depth_counters(self, text: str):
        """If we forcibly flush text, track paren/brace depth for next chunk."""
        for ch in text:
            if ch == '(':
                self.paren_depth += 1
                self.state = "in_paren"
            elif ch == ')':
                self.paren_depth -= 1
                if self.paren_depth < 0:
                    self.paren_depth = 0
                if self.paren_depth == 0 and self.brace_depth == 0:
                    self.state = "outside"
            elif ch == '{':
                self.brace_depth += 1
                self.state = "in_brace"
            elif ch == '}':
                self.brace_depth -= 1
                if self.brace_depth < 0:
                    self.brace_depth = 0
                if self.brace_depth == 0 and self.paren_depth == 0:
                    self.state = "outside"

    def flush_remaining(self) -> Optional[str]:
        """Flush leftover text at the end of the stream."""
        if self.partial_buffer:
            leftover = self.partial_buffer
            self.partial_buffer = ""
            self._update_depth_counters(leftover)
            return leftover
        return None
