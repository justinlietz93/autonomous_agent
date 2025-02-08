# context_manager.py
# Manages session context storage (logs, state, reasoning transcripts).

import os
import glob
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class ContextStorage:
    # Stores detailed context from each interaction.

    MAX_LOG_FILES = 10

    def __init__(self, storage_dir: str = "context_outputs"):
        self.storage_dir = Path(storage_dir)
        self.current_session_id = None
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
        try:
            os.makedirs(self.storage_dir, exist_ok=True)
            converted_state = convert_sets_to_lists(state)
            temp_file = os.path.join(self.storage_dir, "temp_context.json")
            filepath = os.path.join(
                self.storage_dir,
                f"context_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(temp_file, "w", encoding='utf-8') as f:
                json.dump({
                    "session_id": session_id,
                    "response": response,
                    "state": converted_state,
                    "reasoning": reasoning,
                    "tool_use": tool_use or [],
                    "findings": findings or {},
                    "tool_results": tool_results or [],
                    "timestamp": datetime.now().isoformat()
                }, f, indent=2)
            os.replace(temp_file, filepath)
        except Exception as e:
            print(f"Error saving context => {e}")
            error_data = {
                "error": str(e),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            os.makedirs("context_errors", exist_ok=True)
            with open(f"context_errors/{session_id}_error.json", "w") as f:
                json.dump(error_data, f)

    def get_latest_context(self, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        try:
            pattern = f"context_{session_id if session_id else '*'}_*.json"
            files = list(self.storage_dir.glob(pattern))
            if not files:
                return None
            latest = max(files, key=lambda p: p.stat().st_mtime)
            with open(latest) as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading latest context => {e}")
            return None

    def set_session_id(self, session_id: str) -> None:
        self.current_session_id = session_id

    def get_continuation_context(self, session_id: str) -> Dict:
        files = sorted(
            self.storage_dir.glob(f"context_{session_id}_*.json"),
            key=lambda p: p.stat().st_mtime
        )
        if not files:
            return {}
        context_entries = []
        for f in files[:-1]:
            with open(f) as fd:
                data = json.load(fd)
                context_entries.append({
                    "timestamp": data["timestamp"],
                    "response": data["response"],
                    "findings": data.get("findings", {})
                })
        return {
            "history": context_entries,
            "current": files[-1].read_text()
        }

    def get_full_context(self, session_id: str) -> str:
        files = sorted(
            self.storage_dir.glob(f"context_{session_id}_*.json"),
            key=lambda p: p.stat().st_mtime
        )
        context = []
        for f in files:
            with open(f) as fd:
                data = json.load(fd)
                snippet = (
                    f"=== {data['timestamp']} ===\n"
                    f"Response: {data['response']}\n"
                    f"State: {json.dumps(data['state'], indent=2)}\n"
                    f"Tools Used: {', '.join(data.get('tool_use', []))}"
                )
                context.append(snippet)
        return "\n\n".join(context)
