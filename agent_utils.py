"""
工具函数模块
包含终端命令执行等通用工具
"""

import subprocess
from typing import Dict
from agent_config import DANGEROUS_COMMANDS, COMMAND_TIMEOUT, WORKING_DIRECTORY
from agent_memory import memory


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
    
    # 检查危险命令
    for dangerous in DANGEROUS_COMMANDS:
        if dangerous in command.lower():
            return {
                "success": False,
                "output": "",
                "error": f"⚠️ 拒绝执行危险命令: {command}"
            }
    
    # 确定工作目录 - 如果配置的路径不存在，使用当前目录
    work_dir = WORKING_DIRECTORY
    if not os.path.exists(work_dir):
        work_dir = os.getcwd()
    
    # Windows 下使用 GBK 编码，其他系统使用 UTF-8
    import platform
    encoding = 'gbk' if platform.system() == 'Windows' else 'utf-8'
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding=encoding,
            errors='replace',
            timeout=COMMAND_TIMEOUT,
            cwd=work_dir
        )
        
        output = result.stdout if result.stdout else "(命令执行成功，无输出)"
        
        # 记录到命令历史
        memory.add_command(command, output, result.returncode == 0)
        
        return {
            "success": result.returncode == 0,
            "output": output,
            "error": result.stderr
        }
    
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": f"⏱️ 命令执行超时(>{COMMAND_TIMEOUT}秒)"
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": f"❌ 执行失败: {str(e)}"
        }
