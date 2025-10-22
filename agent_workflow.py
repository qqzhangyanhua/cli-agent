"""
工作流构建模块 - 充分利用 LangChain 和 LangGraph 特性
"""

from langgraph.graph import StateGraph, END
from agent_config import AgentState
from agent_nodes import (
    file_reference_processor,
    command_generator,
    command_executor,
    multi_step_planner,
    file_creator,
    multi_command_executor,
    mcp_tool_planner,
    mcp_tool_executor,
    response_formatter,
    question_answerer,
    data_conversion_processor,
    environment_diagnostic_processor,
    git_add_node,
    git_commit_message_generator_node,
    git_commit_executor_node,
    git_pull_node,
    git_push_node,
)
from agent_tool_calling import simple_tool_calling_node


# ============================================
# 路由函数
# ============================================

def route_by_intent(state: AgentState) -> str:
    """
    根据意图路由
    待办/git_commit/code_review 相关已经在 tool_calling 节点完成，直接结束
    auto_commit 需要走 Git 提交工作流（3步骤）
    full_git_workflow 需要走完整 Git 工作流（5步骤：pull -> add -> commit -> push）
    git_pull/git_push 单独处理
    data_conversion/environment_diagnostic 需要专门节点处理
    """
    intent = state["intent"]

    if intent in ["add_todo", "query_todo", "git_commit", "code_review", "git_pull", "git_push"]:
        # 工具调用节点已完成处理，直接结束
        return "end"
    elif intent == "auto_commit":
        # Git 自动提交工作流（3步骤：add -> commit）
        return "git_add"
    elif intent == "full_git_workflow":
        # Git 完整工作流（5步骤：pull -> add -> commit -> push）
        return "git_pull"
    elif intent == "data_conversion":
        # 数据转换需要专门处理
        return "process_data_conversion"
    elif intent == "environment_diagnostic":
        # 环境诊断需要专门处理
        return "process_env_diagnostic"
    elif intent == "terminal_command":
        return "generate_command"
    elif intent == "multi_step_command":
        return "plan_steps"
    elif intent == "mcp_tool_call":
        return "plan_mcp_tool"
    elif intent == "question":
        # 如果 response 已生成（普通问答），直接结束
        if state.get("response"):
            return "end"
        return "answer_question"
    else:
        return "format_response"


def route_after_planning(state: AgentState) -> str:
    """规划后的路由"""
    if state.get("needs_file_creation", False):
        return "create_file"
    else:
        return "execute_multi_commands"


def route_after_git_add(state: AgentState) -> str:
    """Git add 后的路由"""
    if state.get("git_add_success", False):
        return "generate_commit_message"
    else:
        return "end"  # 失败则直接结束


def route_after_commit_message(state: AgentState) -> str:
    """生成 commit 消息后的路由"""
    if state.get("git_commit_message_generated", False):
        return "execute_commit"
    else:
        return "end"  # 失败则直接结束


def route_after_pull(state: AgentState) -> str:
    """Git pull 后的路由"""
    if state.get("git_pull_success", False):
        # Pull 成功，继续 add
        return "git_add"
    else:
        return "end"  # Pull 失败则直接结束


def route_after_commit(state: AgentState) -> str:
    """Commit 后的路由 - 判断是否需要 push"""
    intent = state.get("intent", "")
    
    if intent == "full_git_workflow":
        # 完整工作流需要继续 push
        if state.get("git_commit_success", False):
            return "git_push"
        else:
            return "end"  # Commit 失败则结束
    else:
        # auto_commit 只到 commit，不 push
        return "end"


# ============================================
# 构建工作流
# ============================================

def build_agent() -> StateGraph:
    """
    构建AI智能体工作流 - 充分利用 LangChain 工具调用特性

    核心改进：
    1. 使用 LangChain Tool Calling 替代硬编码意图分析
    2. LLM 自主选择工具并调用
    3. 简化工作流，减少不必要的节点
    """

    workflow = StateGraph(AgentState)

    # 添加所有节点
    workflow.add_node("process_file_references", file_reference_processor)
    workflow.add_node("tool_calling", simple_tool_calling_node)  # 新：智能工具调用
    workflow.add_node("generate_command", command_generator)
    workflow.add_node("execute_command", command_executor)
    workflow.add_node("plan_steps", multi_step_planner)
    workflow.add_node("create_file", file_creator)
    workflow.add_node("execute_multi_commands", multi_command_executor)
    workflow.add_node("plan_mcp_tool", mcp_tool_planner)
    workflow.add_node("execute_mcp_tool", mcp_tool_executor)
    workflow.add_node("format_response", response_formatter)
    workflow.add_node("answer_question", question_answerer)
    workflow.add_node("process_data_conversion", data_conversion_processor)
    workflow.add_node("process_env_diagnostic", environment_diagnostic_processor)
    # Git 工作流节点
    workflow.add_node("git_pull", git_pull_node)
    workflow.add_node("git_add", git_add_node)
    workflow.add_node("generate_commit_message", git_commit_message_generator_node)
    workflow.add_node("execute_commit", git_commit_executor_node)
    workflow.add_node("git_push", git_push_node)

    # 设置入口
    workflow.set_entry_point("process_file_references")

    # 新流程：文件引用 -> 工具调用（智能分析意图）
    workflow.add_edge("process_file_references", "tool_calling")

    # 工具调用后根据意图路由
    workflow.add_conditional_edges(
        "tool_calling",
        route_by_intent,
        {
            "end": END,  # 待办/git_commit/code_review/git_pull/git_push 直接结束
            "git_add": "git_add",  # Git 自动提交工作流（3步骤）
            "git_pull": "git_pull",  # Git 完整工作流（5步骤）
            "process_data_conversion": "process_data_conversion",
            "process_env_diagnostic": "process_env_diagnostic",
            "generate_command": "generate_command",
            "plan_steps": "plan_steps",
            "plan_mcp_tool": "plan_mcp_tool",
            "answer_question": "answer_question",
            "format_response": "format_response"
        }
    )

    # 终端命令路径
    workflow.add_edge("generate_command", "execute_command")
    workflow.add_edge("execute_command", "format_response")

    # 多步骤命令路径
    workflow.add_conditional_edges(
        "plan_steps",
        route_after_planning,
        {
            "create_file": "create_file",
            "execute_multi_commands": "execute_multi_commands"
        }
    )
    workflow.add_edge("create_file", "execute_multi_commands")
    workflow.add_edge("execute_multi_commands", "format_response")

    # MCP工具路径
    workflow.add_edge("plan_mcp_tool", "execute_mcp_tool")
    workflow.add_edge("execute_mcp_tool", "format_response")

    # 数据转换和环境诊断路径
    workflow.add_edge("process_data_conversion", END)
    workflow.add_edge("process_env_diagnostic", END)

    # Git 完整工作流路径（5步骤）
    # pull -> add -> generate_message -> commit -> push
    workflow.add_conditional_edges(
        "git_pull",
        route_after_pull,
        {
            "git_add": "git_add",
            "end": END
        }
    )
    
    # Git 提交工作流路径（共用：add -> generate_message -> commit）
    workflow.add_conditional_edges(
        "git_add",
        route_after_git_add,
        {
            "generate_commit_message": "generate_commit_message",
            "end": END
        }
    )
    workflow.add_conditional_edges(
        "generate_commit_message",
        route_after_commit_message,
        {
            "execute_commit": "execute_commit",
            "end": END
        }
    )
    
    # Commit 后路由：根据 intent 决定是否继续 push
    workflow.add_conditional_edges(
        "execute_commit",
        route_after_commit,
        {
            "git_push": "git_push",
            "end": END
        }
    )
    
    # Push 完成后结束
    workflow.add_edge("git_push", END)

    # 结束节点
    workflow.add_edge("format_response", END)
    workflow.add_edge("answer_question", END)

    return workflow.compile()
