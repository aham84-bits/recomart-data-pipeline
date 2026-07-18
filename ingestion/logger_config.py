# Configures logging for the ingestion module
import logging
import os
from logging.handlers import RotatingFileHandler

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

def get_logger(name):
    # Get a logger with the given name
    logger = logging.getLogger(name)
    
    # Only set up handlers if they haven't been set up yet
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Format: timestamp, level, message
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # File handler with rotation (2MB max, 3 backups)
        file_handler = RotatingFileHandler(
            'logs/ingestion.log',
            maxBytes=2*1024*1024,  # 2MB
            backupCount=3
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger
