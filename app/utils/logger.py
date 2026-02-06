import logging
import os

def setup_logger(app):
    """Set up application logging"""
    log_level = app.config.get('LOG_LEVEL', 'INFO')

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Add file handler if LOG_FILE is configured
    log_file = app.config.get('LOG_FILE')
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        app.logger.addHandler(file_handler)

    app.logger.info("Logger initialized")
