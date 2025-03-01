from typing import Dict, Any, Generator

class TemplateProvider:
    def stream(self, params: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        # Reset parser state at the beginning of each stream
        if self.parser:
            try:
                self.parser.reset()
                self.chunker.flush_remaining()  # Reset chunker state too
            except Exception as e:
                print(f"Warning: Could not reset parser: {e}") 