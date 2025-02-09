from queue import Queue
import time
from typing import Generator

class StreamSmoother:
    """Utility class to smooth streaming output from LLMs."""
    
    def __init__(self, initial_delay: int = 32, zero_delay_queue_size: int = 64):
        self.initial_delay = initial_delay
        self.zero_delay_queue_size = zero_delay_queue_size

    def calculate_delay(self, queue_size: int) -> int:
        """Calculate delay based on queue size."""
        return max(0, int(self.initial_delay - (self.initial_delay / self.zero_delay_queue_size) * queue_size))

    def smooth_stream(self, text: str) -> Generator[str, None, None]:
        """Split text into smaller chunks with calculated delays."""
        queue = Queue()
        
        # Split into characters
        for char in text:
            queue.put(char)
            
            # Calculate and apply delay
            delay = self.calculate_delay(queue.qsize())
            if delay > 0:
                time.sleep(delay / 1000)  # Convert to seconds
            
            yield char 