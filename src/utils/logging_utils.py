#  Copyright (c) 2025.

import logging
import logging.handlers
import os

LOGS_DIR = "logs"
_LOGGING_CONFIGURED = False


def get_logger(name, debug: bool = True):
    _ensure_logs_dir()
    setup_logger(debug=debug)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.propagate = True

    if logger.handlers:
        logger.handlers.clear()

    return logger


def setup_logger(debug: bool = True) -> logging.Logger:
    global _LOGGING_CONFIGURED
    root_logger = logging.getLogger()

    if _LOGGING_CONFIGURED:
        return root_logger

    _ensure_logs_dir()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)

    if not _has_console_handler(root_logger):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter())
        root_logger.addHandler(console_handler)

    detailed_path = os.path.abspath(os.path.join(LOGS_DIR, "detailed.log"))
    if not _has_rotating_handler(root_logger, detailed_path):
        file_handler = logging.handlers.RotatingFileHandler(
            filename=detailed_path,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG if debug else logging.INFO)
        file_handler.setFormatter(detailed_formatter())
        root_logger.addHandler(file_handler)

    error_path = os.path.abspath(os.path.join(LOGS_DIR, "error.log"))
    if not _has_rotating_handler(root_logger, error_path):
        error_file_handler = logging.handlers.RotatingFileHandler(
            filename=error_path,
            maxBytes=10 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8"
        )
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(detailed_formatter())
        root_logger.addHandler(error_file_handler)

    _LOGGING_CONFIGURED = True
    return root_logger


def _ensure_logs_dir():
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)


def _has_console_handler(logger: logging.Logger) -> bool:
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            return True
    return False


def _has_rotating_handler(logger: logging.Logger, filename: str) -> bool:
    target = os.path.abspath(filename)
    for handler in logger.handlers:
        if isinstance(handler, logging.handlers.RotatingFileHandler):
            handler_path = os.path.abspath(getattr(handler, "baseFilename", ""))
            if handler_path == target:
                return True
    return False


def simple_formatter():
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    return formatter


def detailed_formatter():
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(funcName)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return formatter
