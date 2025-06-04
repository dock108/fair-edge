"""
Structured logging configuration for bet-intel application
Sets up JSON logging with contextual information for production observability
"""
import logging
import logging.config
import os
from pathlib import Path
from typing import Any, Dict

import structlog
import yaml


def load_logging_config() -> Dict[str, Any]:
    """Load logging configuration from YAML file"""
    config_path = os.getenv("LOG_CONFIG_PATH", "core/log_config.yaml")
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        # Fallback to basic configuration if YAML file is missing
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'json': {
                    'class': 'structlog.stdlib.ProcessorFormatter',
                    'processor': 'structlog.processors.JSONRenderer'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter': 'json',
                    'stream': 'ext://sys.stdout'
                }
            },
            'root': {
                'level': 'INFO',
                'handlers': ['console']
            }
        }


def setup_structlog():
    """Configure structlog with production-ready processors"""
    # Determine if we're in production or development
    is_production = os.getenv("APP_ENV", "dev").lower() in ("prod", "production")
    
    # Base processors for all environments
    processors = [
        # Add contextvars (request ID, user ID, etc.)
        structlog.contextvars.merge_contextvars,
        
        # Add log level
        structlog.processors.add_log_level,
        
        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso"),
        
        # Add caller info in development
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ) if not is_production else structlog.processors.CallsiteParameterAdder(),
        
        # Stack info for exceptions
        structlog.processors.StackInfoRenderer(),
        
        # Format exceptions
        structlog.dev.set_exc_info,
    ]
    
    # Add JSON renderer for production, console for development
    if is_production:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def setup_logging():
    """Setup complete logging configuration"""
    # Ensure logs directory exists
    logs_dir = Path("/app/logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Load and apply logging configuration
    config = load_logging_config()
    logging.config.dictConfig(config)
    
    # Setup structlog
    setup_structlog()
    
    # Create application logger
    logger = structlog.get_logger("app.setup")
    logger.info("Logging configuration complete", 
                config_file=os.getenv("LOG_CONFIG_PATH", "core/log_config.yaml"),
                production_mode=os.getenv("APP_ENV", "dev") in ("prod", "production"))
    
    return logger


def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get a configured structlog logger instance"""
    return structlog.get_logger(name or __name__)


def add_request_context(request_id: str = None, user_id: str = None, 
                        endpoint: str = None, **kwargs):
    """Add request context to all log messages in this scope"""
    context = {}
    if request_id:
        context["request_id"] = request_id
    if user_id:
        context["user_id"] = user_id
    if endpoint:
        context["endpoint"] = endpoint
    
    # Add any additional context
    context.update(kwargs)
    
    # Use structlog's contextvars to add context
    for key, value in context.items():
        structlog.contextvars.bind_contextvars(**{key: value})


def clear_request_context():
    """Clear request context"""
    structlog.contextvars.clear_contextvars()


# Example usage decorators for FastAPI
def log_request_response():
    """Decorator to log request/response for FastAPI endpoints"""
    
    def decorator(func):
        import functools

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            logger = get_logger(f"endpoint.{func.__name__}")
            
            # Log request start
            logger.info("Request started", 
                        endpoint=func.__name__, 
                        args_count=len(args),
                        kwargs_keys=list(kwargs.keys()))
            
            try:
                result = await func(*args, **kwargs)
                logger.info("Request completed successfully", 
                            endpoint=func.__name__)
                return result
            except Exception as e:
                logger.error("Request failed", 
                             endpoint=func.__name__,
                             error=str(e),
                             error_type=type(e).__name__)
                raise
        return wrapper
    return decorator 