"""
AI智能体配置模块
包含所有配置信息和常量
"""

from typing import TypedDict, Literal, Optional

# ============================================
# LLM配置
# ============================================

# 通用LLM配置 - 用于意图分析、问答等
LLM_CONFIG = {
    "model": "kimi-k2-0905-preview",
    "base_url": "https://api.moonshot.cn/v1",
    "api_key": "sk-6xmKFtCUO7Z3qJnIoAa8D3lI6DJTfvzSYxMbafNT2FFHFDwd",
    "temperature": 0,
}

# 代码生成专用LLM配置 - 用于生成命令和代码
LLM_CONFIG2 = {
    "model": "claude-3-5-sonnet",
    "base_url": "https://sdwfger.edu.kg/v1",
    "api_key": "sk-lCVcio0vmI5U16K1ru9gdJ7ZsszU3lsKnUurlNjhROjWLwxU",
    "temperature": 0,
}

# 默认请求头
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# ============================================
# 工作目录配置
# ============================================

WORKING_DIRECTORY = "/Users/zhangyanhua/Desktop/AI/tushare/quantification/example"

# ============================================
# 安全配置
# ============================================

# 危险命令列表
DANGEROUS_COMMANDS = ["rm -rf", "sudo rm", "chmod 777", "format", "del /f"]

# 命令执行超时（秒）
COMMAND_TIMEOUT = 10

# ============================================
# 记忆配置
# ============================================

# 最大对话历史数量
MAX_CONVERSATION_HISTORY = 10

# 最大命令历史数量
MAX_COMMAND_HISTORY = 20

# ============================================
# 状态类型定义
# ============================================

class AgentState(TypedDict):
    """智能体状态"""
    user_input: str
    intent: Literal["terminal_command", "multi_step_command", "mcp_tool_call", "git_commit", "question", "add_todo", "query_todo", "data_conversion", "environment_diagnostic", "unknown"]
    command: str
    commands: list
    command_output: str
    command_outputs: list
    response: str
    error: str
    needs_file_creation: bool
    file_path: str
    file_content: str
    chat_history: list
    # MCP相关字段
    mcp_tool: str
    mcp_params: dict
    mcp_result: str
    # 文件引用相关字段
    original_input: str
    referenced_files: list
    file_contents: dict
    # 待办事项相关字段
    todo_action: str
    todo_date: str
    todo_time: str
    todo_content: str
    todo_result: str
    # 数据转换相关字段
    data_conversion_type: str
    source_format: str
    target_format: str
    conversion_result: str
    # 环境诊断相关字段
    diagnostic_result: str
