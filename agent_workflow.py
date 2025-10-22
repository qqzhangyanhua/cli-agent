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
)
from agent_tool_calling import simple_tool_calling_node


# ============================================
# 路由函数
# ============================================

def route_by_intent(state: AgentState) -> str:
    """
    根据意图路由
    待办/git_commit/code_review 相关已经在 tool_calling 节点完成，直接结束
    """
    intent = state["intent"]

    if intent in ["add_todo", "query_todo", "git_commit", "code_review"]:
        # 工具调用节点已完成处理，直接结束
        return "end"
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

    # 设置入口
    workflow.set_entry_point("process_file_references")

    # 新流程：文件引用 -> 工具调用（智能分析意图）
    workflow.add_edge("process_file_references", "tool_calling")

    # 工具调用后根据意图路由
    workflow.add_conditional_edges(
        "tool_calling",
        route_by_intent,
        {
            "end": END,  # 待办/git_commit/普通问答 直接结束
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

    # 结束节点
    workflow.add_edge("format_response", END)
    workflow.add_edge("answer_question", END)

    return workflow.compile()
