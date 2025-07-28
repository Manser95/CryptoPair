import logging
import sys
from typing import Any, Dict
from pythonjsonlogger import jsonlogger
from .config import settings


class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = 'no-correlation-id'
        return True


def setup_logging():
    log_level = getattr(logging, settings.log_level.upper())
    
    # Remove all handlers
    logger = logging.getLogger()
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Format based on settings
    if settings.log_format == "json":
        formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(name)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    handler.addFilter(CorrelationIdFilter())
    
    # Configure root logger
    logger.setLevel(log_level)
    logger.addHandler(handler)
    
    # Adjust third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


# Initialize logging on import
logger = setup_logging()