import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    """Configure logging for the application"""
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Configure the root logger
    log_level = logging.DEBUG if app.config.get('DEBUG', False) else logging.INFO
    
    # Create a formatter
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure file handler for all logs
    file_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'rankrite.log'),
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # Configure error file handler for errors only
    error_file_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'error.log'),
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter)
    
    # Configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Get the application logger
    app_logger = logging.getLogger('rankrite')
    app_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    app_logger.handlers = []
    
    # Add handlers to the logger
    app_logger.addHandler(file_handler)
    app_logger.addHandler(error_file_handler)
    app_logger.addHandler(console_handler)
    
    # Set propagation to False to avoid duplicate logs
    app_logger.propagate = False
    
    # Log application startup
    app_logger.info('Application startup')
    
    return app_logger