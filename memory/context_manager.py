# context_manager.py
# Manages session context storage (logs, state, reasoning transcripts).

#TODO: Implement a singleton context manager that can be used to store the context of the session.

import os
from datetime import datetime
import random
import string
from typing import Dict, Any, Optional
from pathlib import Path

class ContextStorage:

    # Stores detailed context from each interaction.
    MAX_LOG_FILES = 10

    def __init__(self, storage_dir: str = "context_outputs"):
        self.storage_dir = Path(storage_dir)
        self.current_session_id = None
        self.log_file = None
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            self._cleanup_old_files()
        except Exception as e:
            print(f"Error creating context storage directory: {e}")
            self.storage_dir = Path("./context_outputs_fallback")
            self.storage_dir.mkdir(exist_ok=True)

    def _cleanup_old_files(self) -> None:
        try:
            files = list(self.storage_dir.glob("context_*.json"))
            if len(files) <= self.MAX_LOG_FILES:
                return
            files.sort(key=lambda p: p.stat().st_mtime)
            for file in files[:-self.MAX_LOG_FILES]:
                try:
                    file.unlink()
                    print(f"Removed old context file: {file}")
                except Exception as e:
                    print(f"Error removing old file: {file} => {e}")
        except Exception as e:
            print(f"Error during file cleanup => {e}")

    def generate_context_filename(self, prompt_name: str) -> str:
        # Generate random session ID with prompt name
        random_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')

        self.session_id = f"{prompt_name}_{random_chars}"
        self.log_file = os.path.join("memory", "context_logs", f"context_{timestamp_str}_{self.session_id}.txt")
        return self.log_file


    def save_context(
        self,
        session_id: str,
        response: str,
        state: Dict[str, Any],
        reasoning: str = "",
        tool_use: list = None,
        findings: dict = None,
        tool_results: list = None
    ):
        raise NotImplementedError("save_context is not implemented")
