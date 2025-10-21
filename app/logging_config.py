import logging
import sys
from app.config import settings


def setup_logging():
    """Setup logging configuration for production"""
    
    # Set logging level based on debug mode
    level = logging.DEBUG if settings.debug else logging.INFO
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'  # Shorter time format
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Reduce noise from external libraries
    logging.getLogger('telegram.Bot').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str):
    """Get logger with consistent configuration"""
    return logging.getLogger(name)


# Create commonly used loggers
calendar_logger = get_logger('app.calendar')
notification_logger = get_logger('app.notifications')
google_calendar_logger = get_logger('app.google_calendar')
database_logger = get_logger('app.database') 