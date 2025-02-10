import pytest
import shutil
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@pytest.fixture(scope="function")
def demo_sandbox(request):
    """Create a sandbox directory for file operations testing."""
    sandbox = Path(__file__).parent / "test_sandbox"
    sandbox.mkdir(exist_ok=True)
    logger.info(f"Created test sandbox at: {sandbox}")

    def cleanup():
        if sandbox.exists():
            shutil.rmtree(sandbox)
            logger.info("Cleaned up test sandbox")
    request.addfinalizer(cleanup)
    
    return sandbox 