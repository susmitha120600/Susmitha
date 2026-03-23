import sys
import json
from pathlib import Path
from loguru import logger
from typing import Optional
from .config import settings


def serialize_record(record):
    subset = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["module"],
        "function": record["function"],
        "line": record["line"],
    }
    
    if record["exception"]:
        subset["exception"] = {
            "type": record["exception"].type.__name__,
            "value": str(record["exception"].value),
            "traceback": record["exception"].traceback,
        }
    
    return json.dumps(subset)


def json_formatter(record):
    record["extra"]["serialized"] = serialize_record(record)
    return "{extra[serialized]}\n"


def setup_logging(log_level: Optional[str] = None, log_format: Optional[str] = None):
    level = log_level or settings.LOG_LEVEL
    format_type = log_format or settings.LOG_FORMAT
    
    logger.remove()
    
    if format_type == "json":
        logger.add(
            sys.stderr,
            format=json_formatter,
            level=level,
            colorize=False,
        )
        
        log_file = Path(settings.LOG_FILE)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_file,
            format=json_formatter,
            level=level,
            rotation="500 MB",
            retention="10 days",
            compression="zip",
        )
    else:
        log_format_str = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        
        logger.add(
            sys.stderr,
            format=log_format_str,
            level=level,
            colorize=True,
        )
        
        log_file = Path(settings.LOG_FILE)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_file,
            format=log_format_str,
            level=level,
            rotation="500 MB",
            retention="10 days",
            compression="zip",
        )
    
    logger.info(f"Logging configured: level={level}, format={format_type}")
    return logger


def get_logger(name: str):
    return logger.bind(name=name)


setup_logging()
