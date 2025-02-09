import logging
import sys
from datetime import datetime
from pathlib import Path
import inspect
import os

import pytest

# Add project root to Python path first
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

def setup_logging(test_name: str = None):
    """Set up logging for tests with proper file handling."""
    try:
        # Create logs directory in tests/tools/generated_test_logs
        log_dir = Path(__file__).parent / "tools" / "generated_test_logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Use test name if provided, otherwise use generic name
        base_name = test_name.replace("test_", "") if test_name else "test"
        log_file = log_dir / f"{base_name}_{timestamp}.txt"

        # Ensure the file is created and writable
        log_file.touch(mode=0o666)
        if not os.access(log_file, os.W_OK):
            raise PermissionError(f"Cannot write to log file: {log_file}")

        print(f"Logging to: {log_file}", file=sys.stderr)

        # Create a file handler with immediate flush
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Create a console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        # Create a formatter
        formatter = logging.Formatter(
            "%(asctime)s.%(msecs)03d %(levelname)s [%(name)s] %(message)s\n",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Add formatter to handlers
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Get the root logger and configure it
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Remove any existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Add our handlers
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # Create a logger for this test
        logger = logging.getLogger(test_name)
        logger.setLevel(logging.DEBUG)
        
        logger.debug("Logging system initialized")
        return log_file
        
    except Exception as e:
        print(f"Error setting up logging in conftest: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        raise

@pytest.fixture(autouse=True)
def setup_test_logging(request):
    """Set up logging for each test."""
    test_name = request.node.name
    log_file = setup_logging(test_name)
    logger = logging.getLogger(request.node.name)
    
    # Log test docstring if available
    test_func = request.node.obj
    if test_func.__doc__:
        logger.info(f"\nTest Description: {test_func.__doc__.strip()}")
    
    # Log test source code
    source = inspect.getsource(test_func)
    logger.debug(f"\nTest Source:\n{source}")
    
    yield
    
    # Log test completion
    logger.info("\nTest Cleanup and Verification")
    
    # Ensure all handlers flush their buffers
    for handler in logging.getLogger().handlers:
        handler.flush()
    logging.shutdown()

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Generate test reports with detailed logging."""
    outcome = yield
    report = outcome.get_result()
    logger = logging.getLogger(item.name)

    if report.when == "call":
        if report.failed:
            logger.error(f"\nTEST FAILED: {item.name}")
            if call.excinfo:
                logger.error(f"Error Type: {call.excinfo.type.__name__}")
                logger.error(f"Error Value: {call.excinfo.value}")
                logger.error(f"Traceback:\n{call.excinfo.traceback}")
        elif report.passed:
            logger.info(f"\nTEST PASSED: {item.name}")
            if hasattr(item, 'funcargs'):
                for name, value in item.funcargs.items():
                    logger.debug(f"Fixture '{name}' final state: {value}")
        elif report.skipped:
            logger.info(f"\nTEST SKIPPED: {item.name}")
            if report.longrepr:
                logger.info(f"Reason: {report.longrepr}")

@pytest.fixture(autouse=True)
def log_test_timing(request):
    """Log test timing information."""
    logger = logging.getLogger(request.node.name)
    logger.info(f"\n{'='*80}\nSTARTING TEST: {request.node.name}\n{'='*80}")
    start = datetime.now()
    yield
    duration = datetime.now() - start
    logger.info(f"\n{'='*80}\nFINISHED TEST: {request.node.name}")
    logger.info(f"Duration: {duration}")
    logger.info('='*80)
