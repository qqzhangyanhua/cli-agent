"""
工具函数模块
包含终端命令执行等通用工具
"""

import subprocess
import sys
import time
import shlex
from typing import Dict
import src.core.agent_config as config
from src.core.agent_memory import memory
from src.core.logger import get_logger, log_json_event

_log = get_logger("exec")


def _is_risky_command(cmd: str) -> bool:
    """简单判断命令是否存在潜在风险（包含元字符/重定向/多条串接等）"""
    risky_chars = [';', '|', '&', '>', '<', '`', '$', '(', ')']
    return any(c in cmd for c in risky_chars)


def _confirm_execution(cmd: str) -> bool:
    """在交互终端下请求用户确认"""
    if not sys.stdin.isatty():
        return False
    try:
        print(f"⚠️ 即将执行可能有副作用的命令:\n  {cmd}")
        resp = input("是否继续执行? [y/N]: ").strip().lower()
        return resp in ("y", "yes")
    except Exception:
        return False


def _has_allowed_prefix(cmd: str) -> bool:
    """判断命令是否匹配允许前缀（用于跳过确认）。
    匹配规则：命令去首尾空格后以某前缀开头（完整单词）。
    """
    stripped = cmd.strip()
    for prefix in config.SECURITY_ALLOWED_PREFIXES:
        if stripped == prefix or stripped.startswith(prefix + " "):
            return True
    return False


def execute_terminal_command(command: str) -> Dict:
    """
    安全地执行终端命令
    
    Args:
        command: 要执行的命令
    
    Returns:
        {
            "success": bool,
            "output": str,
            "error": str
        }
    """
    import os
    
    # 检查危险命令（黑名单）
    for dangerous in config.DANGEROUS_COMMANDS:
        if dangerous in command.lower():
            return {
                "success": False,
                "output": "",
                "error": f"⚠️ 拒绝执行危险命令: {command}"
            }
    
    # 使用当前实际的工作目录，而不是配置中的固定目录
    work_dir = os.getcwd()
    
    # Windows 下使用 GBK 编码，其他系统使用 UTF-8
    import platform
    encoding = 'gbk' if platform.system() == 'Windows' else 'utf-8'
    
    # 风险命令需要确认
    is_risky = _is_risky_command(command)
    if config.SECURITY_CONFIRM_ON_RISKY and is_risky and not _has_allowed_prefix(command):
        if not _confirm_execution(command):
            return {"success": False, "output": "", "error": "用户取消执行或非交互环境未确认"}

    # 选择 shell 模式
    use_shell = config.SECURITY_SHELL_BY_DEFAULT or is_risky

    started = time.monotonic()
    try:
        if use_shell:
            _log.debug("shell 模式执行: %s", command)
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                encoding=encoding,
                errors='replace',
                timeout=config.COMMAND_TIMEOUT,
                cwd=work_dir
            )
        else:
            _log.debug("无 shell 执行: %s", command)
            result = subprocess.run(
                shlex.split(command),
                shell=False,
                capture_output=True,
                text=True,
                encoding=encoding,
                errors='replace',
                timeout=config.COMMAND_TIMEOUT,
                cwd=work_dir
            )
        
        output = result.stdout if result.stdout else "(命令执行成功，无输出)"
        
        # 记录到命令历史
        memory.add_command(command, output, result.returncode == 0)
        duration_ms = int((time.monotonic() - started) * 1000)

        # 结构化事件
        try:
            log_json_event(_log, "command_exec", {
                "cmd": command,
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "shell": use_shell,
                "cwd": work_dir,
                "duration_ms": duration_ms,
                "out_len": len(output or ""),
                "err_len": len(result.stderr or "") if result.stderr is not None else 0,
            })
        except Exception:
            pass

        return {
            "success": result.returncode == 0,
            "output": output,
            "error": result.stderr,
        }
    
    except subprocess.TimeoutExpired:
        # 结构化事件（超时）
        try:
            duration_ms = int((time.monotonic() - started) * 1000)
            log_json_event(_log, "command_exec", {
                "cmd": command,
                "success": False,
                "returncode": None,
                "shell": use_shell,
                "cwd": work_dir,
                "duration_ms": duration_ms,
                "timeout": True,
            }, level="warning")
        except Exception:
            pass
        return {
            "success": False,
            "output": "",
            "error": f"⏱️ 命令执行超时(>{config.COMMAND_TIMEOUT}秒)"
        }
    except Exception as e:
        # 结构化事件（异常）
        try:
            duration_ms = int((time.monotonic() - started) * 1000)
            log_json_event(_log, "command_exec", {
                "cmd": command,
                "success": False,
                "returncode": None,
                "shell": use_shell,
                "cwd": work_dir,
                "duration_ms": duration_ms,
                "error": str(e),
            }, level="error")
        except Exception:
            pass
        return {
            "success": False,
            "output": "",
            "error": f"❌ 执行失败: {str(e)}"
        }
