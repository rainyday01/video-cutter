"""Logging system for video cutter application."""
import os
import sys
import logging
from datetime import datetime
from pathlib import Path


def get_log_file_path() -> Path:
    """Get the log file path next to the executable or script."""
    # When running from PyInstaller bundle
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys.executable).parent
    else:
        # When running from source
        base_dir = Path(__file__).parent.parent
    
    return base_dir / "log.txt"


def setup_logging() -> logging.Logger:
    """Setup logging to both file and console."""
    logger = logging.getLogger('video_cutter')
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler - always log everything
    log_file = get_log_file_path()
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console handler for debugging
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Write session separator
    logger.info("=" * 60)
    logger.info(f"Session started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Log file: {log_file}")
    logger.info("=" * 60)
    
    return logger


# Global logger instance
_logger: logging.Logger | None = None


def get_logger() -> logging.Logger:
    """Get or create the global logger instance."""
    global _logger
    if _logger is None:
        _logger = setup_logging()
    return _logger


def log(message: str, level: str = 'INFO'):
    """Log a message."""
    logger = get_logger()
    if level == 'DEBUG':
        logger.debug(message)
    elif level == 'WARNING':
        logger.warning(message)
    elif level == 'ERROR':
        logger.error(message)
    else:
        logger.info(message)


def log_exception(exc: Exception, context: str = ""):
    """Log an exception with full traceback."""
    import traceback
    logger = get_logger()
    if context:
        logger.error(f"{context}: {str(exc)}")
    else:
        logger.error(str(exc))
    logger.debug(traceback.format_exc())
