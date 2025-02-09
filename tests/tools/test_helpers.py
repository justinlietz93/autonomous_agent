import sys

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"
CHECK = "✓"
CROSS = "✗"
ARROW = "→"

def print_test_step(description: str, passed: bool = True):
    """Print a test step with pass/fail indicator"""
    mark = f"{GREEN}{CHECK}{RESET}" if passed else f"{RED}{CROSS}{RESET}"
    message = f"{BLUE}{ARROW}{RESET} {mark} {description}"
    print(message, flush=True)
    sys.stdout.flush()  # Force immediate output 