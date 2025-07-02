"""
DocuForge Logging Configuration

This module sets up structured logging for the DocuForge library with different
log levels, formatters, and handlers. It provides functions to customize logging
based on application needs.
"""

import logging
import logging.config
import sys
import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Union


# Default logging configuration
DEFAULT_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s [%(filename)s:%(lineno)d]: %(message)s'
        },
        'json': {
            'format': '%(asctime)s',
            '()': 'docuforge.logging_config.JsonFormatter'
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
        },
        'file': {
            'level': 'DEBUG',
            'formatter': 'detailed',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'docuforge.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
        }
    },
    'loggers': {
        'docuforge': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True
        }
    }
}


class JsonFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as JSON for structured logging.
    """
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if available
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
            
        # Add extra context if available
        if hasattr(record, 'context') and record.context:
            log_data['context'] = record.context
            
        return json.dumps(log_data)


class ContextLogger(logging.LoggerAdapter):
    """
    Logger adapter that adds context information to log messages.
    """
    def process(self, msg, kwargs):
        context = kwargs.pop('context', {})
        if self.extra and 'context' in self.extra:
            # Merge with existing context
            context.update(self.extra['context'])
        
        # Create a new record factory to add context
        old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.context = context
            return record
            
        logging.setLogRecordFactory(record_factory)
        result = msg, kwargs
        # Reset record factory
        logging.setLogRecordFactory(old_factory)
        return result


def get_logger(name: str, context: Optional[Dict[str, Any]] = None) -> logging.Logger:
    """
    Get a logger instance with optional context information.
    
    Args:
        name: The name of the logger, typically __name__ of the module
        context: Optional dictionary of context information to include in all logs
        
    Returns:
        A configured logger or logger adapter with context
    """
    logger = logging.getLogger(name)
    
    if context:
        return ContextLogger(logger, {'context': context})
    return logger


def init_logging(config: Optional[Dict[str, Any]] = None, log_file: Optional[str] = None):
    """
    Initialize logging with custom configuration.
    
    Args:
        config: Optional custom logging configuration dict
        log_file: Optional path to log file (overrides config)
    """
    # Start with default config
    log_config = DEFAULT_CONFIG.copy()
    
    # Override with custom config if provided
    if config:
        for section, section_config in config.items():
            if section in log_config and isinstance(section_config, dict):
                log_config[section].update(section_config)
            else:
                log_config[section] = section_config
    
    # Override log file if specified
    if log_file and 'handlers' in log_config and 'file' in log_config['handlers']:
        log_config['handlers']['file']['filename'] = log_file
        # Make sure file handler is enabled
        if 'docuforge' in log_config['loggers']:
            handlers = log_config['loggers']['docuforge']['handlers']
            if 'file' not in handlers:
                handlers.append('file')
    
    # Apply configuration
    logging.config.dictConfig(log_config)
    
    # Create a global trace ID for this process
    global_logger = get_logger('docuforge')
    global_logger.info(f"DocuForge logging initialized (process ID: {os.getpid()})")


def set_log_level(level: Union[str, int]):
    """
    Set the log level for all DocuForge loggers.
    
    Args:
        level: The log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Convert string level to numeric if needed
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    
    # Update the level for all DocuForge loggers
    for name in logging.root.manager.loggerDict:
        if name.startswith('docuforge'):
            logging.getLogger(name).setLevel(level)


# Generate a unique trace ID for this process
TRACE_ID = str(uuid.uuid4())

# Don't initialize logging automatically to avoid circular imports
# Applications should call init_logging() after imports are complete
