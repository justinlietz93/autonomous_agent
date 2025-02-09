import sys
import threading
import itertools
import time
import signal
import atexit

class Throbber:
    """Simple spinner animation for showing activity."""
    
    def __init__(self, message="Waiting on response"):
        self.running = True
        self.message = message
        self.spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
        self.thread = threading.Thread(target=self._spin)
        self.status_message = None  # Track additional status message
        
        # Register cleanup handlers
        atexit.register(self.stop)
        signal.signal(signal.SIGINT, self._handle_interrupt)
        
    def _handle_interrupt(self, signum, frame):
        self.stop()
        sys.exit(1)
        
    def _spin(self):
        while self.running:
            status = f"\n{self.status_message}\n" if self.status_message else ""
            sys.stdout.write(f"\r{self.message} {next(self.spinner)}{status}")
            sys.stdout.flush()
            time.sleep(0.1)
            
    def start(self):
        sys.stdout.write('\033[?25l')  # Hide cursor
        sys.stdout.flush()
        self.thread.start()
        
    def set_status(self, message: str):
        """Set an additional status message below the throbber."""
        self.status_message = message
        
    def stop(self):
        if self.running:
            self.running = False
            if self.thread.is_alive():
                self.thread.join()
            # Clear both throbber and status lines
            lines_to_clear = 2 if self.status_message else 1
            sys.stdout.write('\r' + ' ' * (len(self.message) + 2))  # Clear throbber line
            if self.status_message:
                sys.stdout.write('\n' + ' ' * len(self.status_message))  # Clear status line
            sys.stdout.write('\r' + '\033[A' * (lines_to_clear - 1))  # Move cursor back up
            sys.stdout.write('\033[?25h')  # Show cursor
            sys.stdout.flush() 