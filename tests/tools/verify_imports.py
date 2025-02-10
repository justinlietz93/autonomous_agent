import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"Python path: {sys.path}")
logger.info(f"Current directory: {Path.cwd()}")

try:
    from tools.parse_formatter import InlineCallParser
    logger.info("Successfully imported InlineCallParser")
except Exception as e:
    logger.error(f"Failed to import InlineCallParser: {e}")

try:
    from tools.tool_parser import RealTimeToolParser
    logger.info("Successfully imported RealTimeToolParser")
except Exception as e:
    logger.error(f"Failed to import RealTimeToolParser: {e}")

try:
    from tools.file_tool import FileTool
    logger.info("Successfully imported FileTool")
except Exception as e:
    logger.error(f"Failed to import FileTool: {e}") 