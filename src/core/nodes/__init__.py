"""
工作流节点模块
包含所有LangGraph节点函数
"""

# 文件引用
from src.core.nodes.file_reference import file_reference_processor

# 意图分析和规划
from src.core.nodes.intent import (
    intent_analyzer,
    command_generator,
    multi_step_planner,
    mcp_tool_planner
)

# 问题回答
from src.core.nodes.question import question_answerer

# 命令执行
from src.core.nodes.command import (
    file_creator,
    command_executor,
    multi_command_executor,
    mcp_tool_executor
)

# 响应格式化
from src.core.nodes.formatter import (
    response_formatter,
    format_mcp_success_response
)

# Git 工作流
from src.core.nodes.git_workflow import (
    git_commit_generator,
    git_add_node,
    git_commit_message_generator_node,
    git_commit_executor_node,
    git_pull_node,
    git_push_node
)

# 待办事项
from src.core.nodes.todo import todo_processor

# 数据转换
from src.core.nodes.data_conversion import data_conversion_processor

# 环境诊断
from src.core.nodes.diagnostic import environment_diagnostic_processor

__all__ = [
    # 文件引用
    "file_reference_processor",

    # 意图分析和规划
    "intent_analyzer",
    "command_generator",
    "multi_step_planner",
    "mcp_tool_planner",

    # 问题回答
    "question_answerer",

    # 命令执行
    "file_creator",
    "command_executor",
    "multi_command_executor",
    "mcp_tool_executor",

    # 响应格式化
    "response_formatter",
    "format_mcp_success_response",

    # Git 工作流
    "git_commit_generator",
    "git_add_node",
    "git_commit_message_generator_node",
    "git_commit_executor_node",
    "git_pull_node",
    "git_push_node",

    # 待办事项
    "todo_processor",

    # 数据转换
    "data_conversion_processor",

    # 环境诊断
    "environment_diagnostic_processor",
]
