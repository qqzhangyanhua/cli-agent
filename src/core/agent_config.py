"""
AI智能体配置模块
包含所有配置信息和常量
"""

import json
import os
from typing import TypedDict, Literal, Optional

# ============================================
# 重新导出新的类型定义
# ============================================
# 新的数据类定义在 agent_types.py 中
# 这里保留 TypedDict 定义以确保向后兼容
from src.core.agent_types import (
    Intent,
    ExecutionContext,
    CommandResult,
    FileContext,
    MCPContext,
    TodoData,
    DataConversionData,
    GitData,
    AgentState as AgentStateDataClass,
    AgentStateDict,
    create_initial_state,
)

# 向后兼容的导出
__all__ = [
    "Intent",
    "ExecutionContext",
    "CommandResult",
    "FileContext",
    "MCPContext",
    "TodoData",
    "DataConversionData",
    "GitData",
    "AgentState",
    "AgentStateDict",
    "create_initial_state",
    "LLM_CONFIG",
    "LLM_CONFIG2",
    "DEFAULT_HEADERS",
    "WORKING_DIRECTORY",
    "DANGEROUS_COMMANDS",
    "COMMAND_TIMEOUT",
    "MAX_CONVERSATION_HISTORY",
    "MAX_COMMAND_HISTORY",
    "DAILY_REPORT_TEMPLATES",
    "DEFAULT_DAILY_REPORT_TEMPLATE", 
    "DAILY_REPORT_DIR",
    "AUTO_SAVE_DAILY_REPORT",
    "SECURITY_CONFIRM_ON_RISKY",
    "SECURITY_SHELL_BY_DEFAULT",
    "SECURITY_ALLOWED_PREFIXES",
    "EMPTY_STATE_MESSAGE",
    "PROCESS_STATE_FILE",
    "PROCESS_HISTORY_FILE",
]

# ============================================
# 配置文件加载
# ============================================

def load_config():
    """
    加载配置文件
    
    Returns:
        dict: 配置字典
    """
    # 按优先级尝试多个可能的配置文件位置
    # 1. 环境变量指定的工作目录
    # 2. 当前工作目录
    # 3. XDG 配置目录（$XDG_CONFIG_HOME/dnm/config.json 或 ~/.config/dnm/config.json）
    # 4. 用户配置目录（~/.dnm/config.json）
    # 5. 模块上级目录（项目根）
    xdg_home = os.environ.get("XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config"))
    possible_paths = [
        os.path.join(os.environ.get("AI_AGENT_WORKDIR", ""), "config.json"),
        os.path.join(os.getcwd(), "config.json"),
        os.path.join(xdg_home, "dnm", "config.json"),
        os.path.join(os.path.expanduser("~"), ".dnm", "config.json"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json"),
    ]
    
    config_path = None
    for path in possible_paths:
        if path and os.path.exists(path):
            config_path = path
            break
    
    if not config_path:
        # 生成友好的错误信息，显示所有尝试的路径
        paths_str = "\n".join([f"  - {path}" for path in possible_paths if path])
        raise FileNotFoundError(
            f"❌ 配置文件不存在，已尝试以下位置:\n{paths_str}\n\n"
            f"💡 解决方案:\n"
            f"  1. 在当前目录或配置目录创建 config.json（示例: cp config.template.json ~/.config/dnm/config.json）\n"
            f"  2. 编辑 config.json 填入你的 API 密钥\n"
            f"  3. 或设置环境变量: export AI_AGENT_WORKDIR=/path/to/project"
        )
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"❌ 配置文件格式错误 ({config_path}): {e}")
    except Exception as e:
        raise Exception(f"❌ 读取配置文件失败 ({config_path}): {e}")

# 加载配置
_config = load_config()

# ============================================
# LLM配置
# ============================================

# 通用LLM配置 - 用于意图分析、问答等
LLM_CONFIG = _config.get("llm_configs", {}).get("primary", {})

# 代码生成专用LLM配置 - 用于生成命令和代码
LLM_CONFIG2 = _config.get("llm_configs", {}).get("secondary", {})

# 默认请求头
DEFAULT_HEADERS = _config.get("headers", {})

# ============================================
# 工作目录配置
# ============================================

WORKING_DIRECTORY = _config.get("working_directory", "") or os.getcwd()

# ============================================
# 安全配置
# ============================================

# 危险命令列表
DANGEROUS_COMMANDS = _config.get("security", {}).get("dangerous_commands", [])

# 命令执行超时（秒）
COMMAND_TIMEOUT = _config.get("security", {}).get("command_timeout", 10)

# 安全执行开关
SECURITY_CONFIRM_ON_RISKY = _config.get("security", {}).get("confirm_on_risky", True)
SECURITY_SHELL_BY_DEFAULT = _config.get("security", {}).get("shell_by_default", False)
SECURITY_ALLOWED_PREFIXES = _config.get("security", {}).get("allowed_command_prefixes", [])

# ============================================
# 记忆配置
# ============================================

# 最大对话历史数量
MAX_CONVERSATION_HISTORY = _config.get("memory", {}).get("max_conversation_history", 10)

# 最大命令历史数量
MAX_COMMAND_HISTORY = _config.get("memory", {}).get("max_command_history", 20)

# ============================================
# 日报配置
# ============================================

# 日报模板类型
DAILY_REPORT_TEMPLATES = _config.get("daily_report", {}).get("templates", ["standard", "technical", "summary"])

# 默认日报模板
DEFAULT_DAILY_REPORT_TEMPLATE = _config.get("daily_report", {}).get("default_template", "standard")

# 日报保存目录
DAILY_REPORT_DIR = _config.get("daily_report", {}).get("directory", "daily_reports")

# 是否自动保存日报文件 - 默认关闭，只生成不保存
AUTO_SAVE_DAILY_REPORT = _config.get("daily_report", {}).get("auto_save", False)

# ============================================
# UI/消息配置
# ============================================

# 统一的空状态提示语
EMPTY_STATE_MESSAGE = _config.get("messages", {}).get("empty_state", "没有运行的项目")

# ============================================
# 进程状态与历史配置
# ============================================

_paths_cfg = _config.get("paths", {})

# 进程状态文件（跟踪当前运行中的进程）
PROCESS_STATE_FILE = _paths_cfg.get(
    "process_state_file",
    os.path.join(os.path.expanduser("~"), ".dnm_processes.json")
)

# 进程历史文件（记录最近运行记录）
PROCESS_HISTORY_FILE = _paths_cfg.get(
    "process_history_file",
    os.path.join(os.path.expanduser("~"), ".dnm_process_history.json")
)

# ============================================
# 状态类型定义
# ============================================

# 向后兼容：AgentState 现在指向 AgentStateDict（用于 LangGraph）
# 新代码应该使用 AgentStateDataClass 和 create_initial_state()
AgentState = AgentStateDict
