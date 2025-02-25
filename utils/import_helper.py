# Helper to handle GUI-dependent imports
import os
import sys
import platform

# Flag to determine if GUI libraries should be loaded
HAS_GUI = False

# Create dummy PyAutoGUI as fallback
class DummyPyAutoGUI:
    def __getattr__(self, name):
        def dummy_method(*args, **kwargs):
            print(f"Warning: PyAutoGUI method '{name}' called but GUI is not available")
            return None
        return dummy_method
    
    def size(self):
        return (1920, 1080)  # Return default screen size

# Try to import real PyAutoGUI
try:
    # For Windows or macOS
    if platform.system() in ['Windows', 'Darwin']:
        import pyautogui
        import mouseinfo
        HAS_GUI = True
    # For Linux with display
    elif os.environ.get('DISPLAY'):
        import pyautogui
        import mouseinfo
        HAS_GUI = True
    else:
        # No GUI available
        pyautogui = DummyPyAutoGUI()
        mouseinfo = None
except Exception as e:
    # Use dummy implementation
    pyautogui = DummyPyAutoGUI()
    mouseinfo = None
    print(f"GUI libraries not available: {e}")

# Add psutil handling
try:
    import psutil
except ImportError:
    # Create dummy psutil with minimal implementation
    class DummyPsUtil:
        def virtual_memory(self):
            class VM: 
                total = 8000000000  # 8GB
                available = 4000000000  # 4GB
                used = 4000000000  # 4GB
                percent = 50.0
            return VM()
        
        def cpu_count(self):
            return 4
            
        def cpu_percent(self, interval=0, percpu=False):
            return [25.0, 30.0, 20.0, 15.0] if percpu else 25.0
            
        def disk_partitions(self):
            return []
            
        def disk_usage(self, path):
            class Usage:
                total = 500000000000  # 500GB
                used = 250000000000   # 250GB
                free = 250000000000   # 250GB
                percent = 50.0
            return Usage()
            
    psutil = DummyPsUtil()
    print("psutil not available, using dummy implementation") 