"""
新工作流 - 充分利用 LangGraph 和 LangChain 的特性
采用更智能的架构：LLM 作为控制中心，工具作为执行单元
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
    question_answerer,
    git_commit_generator,
)
from agent_tool_calling import simple_tool_calling_node


def route_by_intent_v2(state: AgentState) -> str:
    """
    新的路由逻辑
    - 待办相关直接在工具调用节点完成，返回 END
    - 其他意图继续原有流程
    """
    intent = state["intent"]

    if intent in ["add_todo", "query_todo"]:
        # 待办已经在 tool_calling 节点处理完成
        return "end"
    elif intent == "git_commit":
        return "generate_git_commit"
    elif intent == "terminal_command":
        return "generate_command"
    elif intent == "multi_step_command":
        return "plan_steps"
    elif intent == "mcp_tool_call":
        return "plan_mcp_tool"
    elif intent == "question":
        # 如果 response 已生成，直接结束
        if state.get("response"):
            return "end"
        return "answer_question"
    else:
        return "answer_question"


def route_after_planning(state: AgentState) -> str:
    """规划后的路由"""
    if state.get("needs_file_creation", False):
        return "create_file"
    else:
        return "execute_multi_commands"


def build_agent_v2() -> StateGraph:
    """
    构建新的工作流（v2版本）
    核心改进：
    1. 使用 LangChain 工具调用替代硬编码的意图路由
    2. 让 LLM 自主选择工具
    3. 简化状态转换逻辑
    """

    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("process_file_references", file_reference_processor)
    workflow.add_node("tool_calling", simple_tool_calling_node)  # 新增：智能工具调用节点
    workflow.add_node("generate_command", command_generator)
    workflow.add_node("execute_command", command_executor)
    workflow.add_node("plan_steps", multi_step_planner)
    workflow.add_node("create_file", file_creator)
    workflow.add_node("execute_multi_commands", multi_command_executor)
    workflow.add_node("plan_mcp_tool", mcp_tool_planner)
    workflow.add_node("execute_mcp_tool", mcp_tool_executor)
    workflow.add_node("generate_git_commit", git_commit_generator)
    workflow.add_node("answer_question", question_answerer)

    # 设置入口
    workflow.set_entry_point("process_file_references")

    # 文件引用 -> 工具调用（智能分析）
    workflow.add_edge("process_file_references", "tool_calling")

    # 工具调用后根据意图路由
    workflow.add_conditional_edges(
        "tool_calling",
        route_by_intent_v2,
        {
            "end": END,  # 待办相关直接结束
            "generate_git_commit": "generate_git_commit",
            "generate_command": "generate_command",
            "plan_steps": "plan_steps",
            "plan_mcp_tool": "plan_mcp_tool",
            "answer_question": "answer_question",
        }
    )

    # 其他路径保持不变
    workflow.add_edge("generate_command", "execute_command")
    workflow.add_edge("execute_command", END)

    workflow.add_conditional_edges(
        "plan_steps",
        route_after_planning,
        {
            "create_file": "create_file",
            "execute_multi_commands": "execute_multi_commands"
        }
    )
    workflow.add_edge("create_file", "execute_multi_commands")
    workflow.add_edge("execute_multi_commands", END)

    workflow.add_edge("plan_mcp_tool", "execute_mcp_tool")
    workflow.add_edge("execute_mcp_tool", END)

    workflow.add_edge("generate_git_commit", END)
    workflow.add_edge("answer_question", END)

    return workflow.compile()


# 为了向后兼容，保留原有接口
def build_agent():
    """向后兼容的接口，使用新的v2工作流"""
    return build_agent_v2()
