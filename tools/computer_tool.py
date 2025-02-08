# computer_tool.py
# Cross-platform tool for controlling mouse, keyboard, system info.

import base64
import io
import os
import time
from enum import Enum
from typing import Dict, Any, Literal, Optional, Tuple

import pyautogui
import platform
import psutil

from .tool_base import Tool

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5

class Action(str, Enum):
    KEY = "key"
    TYPE = "type"
    MOUSE_MOVE = "mouse_move"
    LEFT_CLICK = "left_click"
    RIGHT_CLICK = "right_click"
    MIDDLE_CLICK = "middle_click"
    DOUBLE_CLICK = "double_click"
    SCREENSHOT = "screenshot"
    CURSOR_POSITION = "cursor_position"
    LEFT_CLICK_DRAG = "left_click_drag"
    FIND_WINDOW = "find_window"
    MOVE_WINDOW = "move_window"
    SET_WINDOW_FOCUS = "set_window_focus"
    GET_WINDOW_INFO = "get_window_info"
    SYSTEM_INFO = "system_info"
    MEMORY_INFO = "memory_info"
    CPU_INFO = "cpu_info"
    DISK_INFO = "disk_info"

class ComputerTool(Tool):
    name = "computer"
    description = "A tool for controlling the computer's mouse/keyboard and checking system info."

    @property
    def input_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [e.value for e in Action],
                    "description": "Action to perform"
                },
                "text": {"type": "string"},
                "coordinate": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "minItems": 2,
                    "maxItems": 2
                },
                "window_title": {"type": "string"},
                "position": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "minItems": 2,
                    "maxItems": 2
                },
                "size": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "minItems": 2,
                    "maxItems": 2
                }
            },
            "required": ["action"]
        }

    def __init__(self):
        super().__init__()
        self.screen_width, self.screen_height = pyautogui.size()
        self.os_name = platform.system().lower()
        if self.os_name == "windows":
            try:
                import win32api
                import win32con
                import win32gui
                self.win32api = win32api
                self.win32con = win32con
                self.win32gui = win32gui
            except ImportError:
                print("Windows-specific modules not available")
        elif self.os_name == "linux":
            try:
                import Xlib.display
                self.display = Xlib.display.Display()
            except ImportError:
                print("Linux-specific modules not available")

    def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        try:
            action = Action(input["action"])
            text = input.get("text")
            coordinate = input.get("coordinate")
            window_title = input.get("window_title")
            position = input.get("position")
            size = input.get("size")

            # handle system info
            if action == Action.SYSTEM_INFO:
                return self.format_result("", str(self._get_system_info()))
            elif action == Action.MEMORY_INFO:
                return self.format_result("", str(self._get_memory_info()))
            elif action == Action.CPU_INFO:
                return self.format_result("", str(self._get_cpu_info()))
            elif action == Action.DISK_INFO:
                return self.format_result("", str(self._get_disk_info()))
            
            # handle UI actions
            if action == Action.SCREENSHOT:
                b64 = self._take_screenshot()
                return self.format_result("", b64)

            # ... (The rest of the logic is unchanged, removed for brevity) ...

            return self.format_result("", "Action not fully implemented in snippet.")
        except Exception as e:
            return self.format_error("", f"{str(e)}")

    def _get_system_info(self) -> Dict:
        import platform
        return {
            "os": platform.system(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "hostname": platform.node()
        }

    def _get_memory_info(self) -> Dict:
        mem = psutil.virtual_memory()
        return {"total": mem.total, "available": mem.available, "used": mem.used, "percent": mem.percent}

    def _get_cpu_info(self) -> Dict:
        return {
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1, percpu=True),
            "cpu_freq": str(psutil.cpu_freq())
        }

    def _get_disk_info(self) -> Dict:
        disk_info = {}
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_info[partition.mountpoint] = {
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": usage.percent
                }
            except:
                pass
        return disk_info

    def _take_screenshot(self) -> str:
        import io, base64
        screenshot = pyautogui.screenshot()
        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
