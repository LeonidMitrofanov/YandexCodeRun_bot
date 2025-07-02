from typing import List, Dict, Any
from pathlib import Path
import logging.config

class MainConfig:
    INCLUDE_GENERAL: bool = True
    LANGUAGES: List[str] = [
        'python', 'c', 'c-plus-plus', 'c-sharp', 'java', 'javascript',
        'kotlin', 'swift', 'go', 'rust', 'dart', 'pascal'
    ]
    DATETIME_FORMAT: str = "%H:%M %d.%m.%Y"
    LOG_DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


    STORAGE_DIR: Path = Path("core/storage")
    LOGS_DIR: Path = STORAGE_DIR / "logs"

    MAX_LOG_SIZE: int = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT: int = 5
    LOG_LEVEL: str = "INFO"  # "DEBUG"

    LOG_CONFIG: Dict[str, Any] = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "verbose": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                },
                "simple": {
                    "format": "%(levelname)s - %(message)s"
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "simple",
                    "level": LOG_LEVEL,
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": "verbose",
                    "filename": f"{LOGS_DIR}/app.log",
                    "maxBytes": MAX_LOG_SIZE,
                    "backupCount": LOG_BACKUP_COUNT,
                    "encoding": "utf8",
                    "level": LOG_LEVEL
                },
                "error_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": "verbose",
                    "filename": f"{LOGS_DIR}/error.log",
                    "maxBytes": MAX_LOG_SIZE,
                    "backupCount": LOG_BACKUP_COUNT,
                    "encoding": "utf8",
                    "level": "ERROR"
                }
            },
            "loggers": {
                "": { 
                    "handlers": ["console", "file", "error_file"],
                    "level": LOG_LEVEL,
                },
                "core": {
                    "level": LOG_LEVEL,
                    "propagate": True
                },
                "bot": {
                    "level": LOG_LEVEL,
                    "propagate": True
                },
                "parser": {
                    "level": LOG_LEVEL,
                    "propagate": True
                },
                "aiogram.dispatcher": {
                    "level": "CRITICAL",
                    "propagate": True
                },
                "aiogram.event": {
                    "level": "CRITICAL",
                    "propagate": True
                },
                "matplotlib.category": {
                    "level": "CRITICAL",
                    "propagate": True
                }
            }
        }
    @classmethod
    def setup_logging(cls):
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        logging.config.dictConfig(cls.LOG_CONFIG)