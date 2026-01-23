# app/utils/logger.py
"""
Centralized logging configuration using Loguru.
Bridges standard library logging to Loguru for unified log handling.
"""

import logging
import sys
from pathlib import Path

from loguru import logger


class InterceptHandler(logging.Handler):
    """
    Handler that intercepts standard library logging and redirects to Loguru.
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging(
    level: str = "INFO",
    log_file: str | None = None,
    json_logs: bool = False,
) -> None:
    """
    Configure Loguru as the main logging handler.
    
    Args:
        level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
        json_logs: If True, output logs in JSON format
    """
    # Remove default handler
    logger.remove()

    # Console format
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Add console handler
    logger.add(
        sys.stderr,
        format=log_format if not json_logs else None,
        level=level,
        serialize=json_logs,
        backtrace=True,
        diagnose=True,
    )

    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            format=log_format if not json_logs else None,
            level=level,
            serialize=json_logs,
            rotation="10 MB",
            retention="30 days",
            compression="gz",
        )

    # Intercept standard library logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Intercept specific loggers
    for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access", "sqlalchemy"]:
        logging.getLogger(logger_name).handlers = [InterceptHandler()]


# Initialize logging on import
setup_logging()

# Export logger for use throughout the application
__all__ = ["logger", "setup_logging"]
