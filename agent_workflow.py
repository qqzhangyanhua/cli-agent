"""
工作流构建模块
"""

from langgraph.graph import StateGraph, END
from agent_config import AgentState
from agent_nodes import (
    intent_analyzer,
    command_generator,
    command_executor,
    multi_step_planner,
    file_creator,
    multi_command_executor,
    mcp_tool_planner,
    mcp_tool_executor,
    response_formatter,
    question_answerer,
    git_commit_generator
)


# ============================================
# 路由函数
# ============================================

def route_by_intent(state: AgentState) -> str:
    """根据意图路由"""
    intent = state["intent"]
    if intent == "terminal_command":
        return "generate_command"
    elif intent == "multi_step_command":
        return "plan_steps"
    elif intent == "mcp_tool_call":
        return "plan_mcp_tool"
    elif intent == "git_commit":
        return "generate_git_commit"
    elif intent == "question":
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
    """构建AI智能体工作流"""
    
    workflow = StateGraph(AgentState)
    
    # 添加所有节点
    workflow.add_node("analyze_intent", intent_analyzer)
    workflow.add_node("generate_command", command_generator)
    workflow.add_node("execute_command", command_executor)
    workflow.add_node("plan_steps", multi_step_planner)
    workflow.add_node("create_file", file_creator)
    workflow.add_node("execute_multi_commands", multi_command_executor)
    workflow.add_node("plan_mcp_tool", mcp_tool_planner)
    workflow.add_node("execute_mcp_tool", mcp_tool_executor)
    workflow.add_node("generate_git_commit", git_commit_generator)  # Git commit生成
    workflow.add_node("format_response", response_formatter)
    workflow.add_node("answer_question", question_answerer)
    
    # 设置入口
    workflow.set_entry_point("analyze_intent")
    
    # 意图路由
    workflow.add_conditional_edges(
        "analyze_intent",
        route_by_intent,
        {
            "generate_command": "generate_command",
            "plan_steps": "plan_steps",
            "plan_mcp_tool": "plan_mcp_tool",
            "generate_git_commit": "generate_git_commit",  # Git commit路径
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
    
    # Git commit路径
    workflow.add_edge("generate_git_commit", END)  # 直接结束，不需要format
    
    # 结束节点
    workflow.add_edge("format_response", END)
    workflow.add_edge("answer_question", END)
    
    return workflow.compile()
