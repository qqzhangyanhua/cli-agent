"""
统一日志模块
提供获取全局 logger 的方法，并支持通过环境变量控制日志级别。
"""

import logging
import os
from typing import Optional


_LOGGER_NAME = "dnm"
_DEFAULT_LEVEL = os.environ.get("DNM_LOG_LEVEL", "INFO").upper()


def _level_from_env(level_str: str) -> int:
    mapping = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "NOTSET": logging.NOTSET,
    }
    return mapping.get(level_str, logging.INFO)


class _RequestIdFilter(logging.Filter):
    """为日志记录注入请求ID（来自环境变量 DNM_REQ_ID）。"""

    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        record.request_id = os.environ.get("DNM_REQ_ID", "-")
        return True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """获取项目统一 logger。

    Args:
        name: 可选子 logger 名称
    """
    logger_name = f"{_LOGGER_NAME}.{name}" if name else _LOGGER_NAME
    logger = logging.getLogger(logger_name)

    if not logging.getLogger(_LOGGER_NAME).handlers:
        # 仅初始化一次根 logger（dnm）
        root = logging.getLogger(_LOGGER_NAME)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(name)s req=%(request_id)s - %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(formatter)
        handler.addFilter(_RequestIdFilter())
        root.addHandler(handler)
        root.setLevel(_level_from_env(_DEFAULT_LEVEL))

    return logger


def set_level(level: str) -> None:
    """动态设置日志级别"""
    logging.getLogger(_LOGGER_NAME).setLevel(_level_from_env(level.upper()))
