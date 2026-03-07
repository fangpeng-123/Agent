# -*- coding: utf-8 -*-
"""结构化日志"""

import json
import logging
from datetime import datetime
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """JSON 格式日志"""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "name": record.name,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        return json.dumps(log_data, ensure_ascii=False)


def setup_logger(
    name: str = "agent",
    level: int = logging.INFO,
    log_file: str = None,
) -> logging.Logger:
    """设置日志"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)

    return logger


logger = setup_logger()
