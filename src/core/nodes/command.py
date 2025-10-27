"""
命令执行节点
包含单命令和多命令执行、文件创建、MCP工具执行
"""

import json
from src.core.agent_config import AgentState
from src.core.agent_utils import execute_terminal_command
from src.mcp.mcp_manager import mcp_manager


def file_creator(state: AgentState) -> dict:
    """创建文件"""
    file_path = state["file_path"]
    file_content = state["file_content"]

    print(f"[文件创建] 创建文件: {file_path}")

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_content)
        print(f"[文件创建] ✅ 成功创建文件: {file_path}")
        return {"error": ""}
    except Exception as e:
        error_msg = f"文件创建失败: {str(e)}"
        print(f"[文件创建] ❌ {error_msg}")
        return {"error": error_msg}


def command_executor(state: AgentState) -> dict:
    """执行单个终端命令"""
    command = state["command"]
    print(f"[执行命令] {command}")

    result = execute_terminal_command(command)

    if result["success"]:
        print(f"[执行成功] 输出长度: {len(result['output'])} 字符")
        return {"command_output": result["output"], "error": ""}
    else:
        print(f"[执行失败] {result['error']}")
        return {"command_output": "", "error": result["error"]}


def multi_command_executor(state: AgentState) -> dict:
    """执行多个终端命令"""
    commands = state["commands"]
    outputs = []

    print(f"[多命令执行] 共{len(commands)}个命令")

    for idx, command in enumerate(commands, 1):
        print(f"[多命令执行] 执行第{idx}个命令: {command}")
        result = execute_terminal_command(command)

        outputs.append(
            {
                "command": command,
                "success": result["success"],
                "output": result["output"],
                "error": result["error"],
            }
        )

        if result["success"]:
            print(f"[多命令执行] ✅ 第{idx}个命令执行成功")
        else:
            print(f"[多命令执行] ❌ 第{idx}个命令执行失败: {result['error']}")

    return {"command_outputs": outputs}


def mcp_tool_executor(state: AgentState) -> dict:
    """执行MCP工具"""
    tool_name = state["mcp_tool"]
    params = state["mcp_params"]

    print(f"[MCP工具执行] 工具: {tool_name}")
    print(f"            参数: {params}")

    try:
        result = mcp_manager.call_tool(tool_name, **params)

        if result.get("success"):
            print(f"[MCP工具执行] ✅ 成功")
        else:
            print(f"[MCP工具执行] ❌ 失败: {result.get('error')}")

        return {"mcp_result": json.dumps(result, ensure_ascii=False)}

    except Exception as e:
        error_result = {"success": False, "error": str(e)}
        print(f"[MCP工具执行] ❌ 异常: {e}")
        return {"mcp_result": json.dumps(error_result, ensure_ascii=False)}
