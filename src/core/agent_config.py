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
    # 尝试多个可能的配置文件位置
    possible_paths = [
        # 1. 项目根目录（相对于此文件）
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json"),
        # 2. 当前工作目录
        os.path.join(os.getcwd(), "config.json"),
        # 3. 环境变量指定的工作目录
        os.path.join(os.environ.get("AI_AGENT_WORKDIR", ""), "config.json"),
        # 4. 用户主目录下的 .ai-agent 目录
        os.path.join(os.path.expanduser("~"), ".ai-agent", "config.json"),
    ]
    
    # 添加项目特定路径（如果在已知项目目录中）
    project_dir = "/Users/zhangyanhua/Desktop/AI/tushare/quantification/example"
    if os.path.exists(project_dir):
        possible_paths.insert(0, os.path.join(project_dir, "config.json"))
    
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
            f"  1. 在项目根目录运行: cp config.template.json config.json\n"
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
LLM_CONFIG = _config["llm_configs"]["primary"]

# 代码生成专用LLM配置 - 用于生成命令和代码
LLM_CONFIG2 = _config["llm_configs"]["secondary"]

# 默认请求头
DEFAULT_HEADERS = _config["headers"]

# ============================================
# 工作目录配置
# ============================================

WORKING_DIRECTORY = _config["working_directory"]

# ============================================
# 安全配置
# ============================================

# 危险命令列表
DANGEROUS_COMMANDS = _config["security"]["dangerous_commands"]

# 命令执行超时（秒）
COMMAND_TIMEOUT = _config["security"]["command_timeout"]

# ============================================
# 记忆配置
# ============================================

# 最大对话历史数量
MAX_CONVERSATION_HISTORY = _config["memory"]["max_conversation_history"]

# 最大命令历史数量
MAX_COMMAND_HISTORY = _config["memory"]["max_command_history"]

# ============================================
# 日报配置
# ============================================

# 日报模板类型
DAILY_REPORT_TEMPLATES = _config["daily_report"]["templates"]

# 默认日报模板
DEFAULT_DAILY_REPORT_TEMPLATE = _config["daily_report"]["default_template"]

# 日报保存目录
DAILY_REPORT_DIR = _config["daily_report"]["directory"]

# 是否自动保存日报文件
AUTO_SAVE_DAILY_REPORT = _config["daily_report"]["auto_save"]

# ============================================
# 状态类型定义
# ============================================

# 向后兼容：AgentState 现在指向 AgentStateDict（用于 LangGraph）
# 新代码应该使用 AgentStateDataClass 和 create_initial_state()
AgentState = AgentStateDict

