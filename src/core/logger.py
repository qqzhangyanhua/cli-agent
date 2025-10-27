"""
统一日志模块
提供获取全局 logger 的方法，并支持通过环境变量控制日志级别。
"""

import logging
from logging.handlers import RotatingFileHandler
import os
from typing import Optional, Dict, Any
import json


_LOGGER_NAME = "dnm"
_DEFAULT_LEVEL = os.environ.get("DNM_LOG_LEVEL", "INFO").upper()
_JSON_LOGGER_NAME = "dnm.json"
_JSON_LOGGER_ENABLED = False


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


def get_request_id() -> str:
    """获取当前请求ID（来自环境变量）。"""
    return os.environ.get("DNM_REQ_ID", "-")


def log_json_event(logger: logging.Logger, event: str, data: Dict[str, Any], level: str = "info") -> None:
    """以 JSON 结构写入一条事件日志。

    message 结构:
      {"event": "<name>", "req": "<request_id>", "data": {...}}
    """
    payload = {"event": event, "req": get_request_id(), "data": data}
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    level = (level or "info").lower()
    if level == "debug":
        logger.debug(text)
    elif level == "warning":
        logger.warning(text)
    elif level == "error":
        logger.error(text)
    else:
        logger.info(text)

    # 同步写入 JSON 文件 logger（若已启用）
    if _JSON_LOGGER_ENABLED:
        jl = logging.getLogger(_JSON_LOGGER_NAME)
        if level == "debug":
            jl.debug(text)
        elif level == "warning":
            jl.warning(text)
        elif level == "error":
            jl.error(text)
        else:
            jl.info(text)


def enable_json_file_logging(path: Optional[str] = None, max_bytes: int = 5 * 1024 * 1024, backup_count: int = 5) -> Optional[str]:
    """启用独立 JSON 日志文件（仅写入 log_json_event 产生的 JSON 文本）。

    Args:
        path: 日志文件路径，默认 ~/.dnm/dnm-structured.log 或 DNM_JSON_LOG_PATH
        max_bytes: 单文件最大大小（默认 5 MiB）
        backup_count: 保留文件个数

    Returns:
        实际使用的日志文件路径（或 None 表示未启用）
    """
    global _JSON_LOGGER_ENABLED

    if os.environ.get("DNM_JSON_LOG_DISABLE", "0") == "1":
        return None

    if path is None:
        path = os.environ.get("DNM_JSON_LOG_PATH")
    if path is None:
        home = os.path.expanduser("~")
        path = os.path.join(home, ".dnm", "dnm-structured.log")

    # 确保目录存在
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    except Exception:
        return None

    jl = logging.getLogger(_JSON_LOGGER_NAME)
    if jl.handlers:
        _JSON_LOGGER_ENABLED = True
        return path

    handler = RotatingFileHandler(path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8")
    # 仅写入原始 JSON 文本
    handler.setFormatter(logging.Formatter(fmt="%(message)s"))
    # 只记录 info 及以上（可按需调整）
    jl.setLevel(_level_from_env(os.environ.get("DNM_JSON_LOG_LEVEL", "INFO").upper()))
    jl.addHandler(handler)
    jl.propagate = False  # 不向上冒泡，避免被控制台 handler 再次处理
    _JSON_LOGGER_ENABLED = True
    return path
