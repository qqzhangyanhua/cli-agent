"""
响应格式化节点
格式化各种类型的响应输出
"""

import json
from src.core.agent_config import AgentState


def response_formatter(state: AgentState) -> dict:
    """格式化最终响应"""
    if state["intent"] == "terminal_command":
        if state.get("error"):
            response = (
                f"❌ 命令执行失败\n\n命令: {state['command']}\n错误: {state['error']}"
            )
        else:
            response = f"✅ 命令执行成功\n\n命令: {state['command']}\n\n输出:\n{state['command_output']}"

    elif state["intent"] == "multi_step_command":
        response = "✅ 多步骤任务执行结果:\n\n"

        if state.get("needs_file_creation"):
            response += f"📄 创建文件: {state.get('file_path', '')}\n\n"

        outputs = state.get("command_outputs", [])
        for idx, output in enumerate(outputs, 1):
            status = "✅" if output["success"] else "❌"
            response += f"{status} 命令 {idx}: {output['command']}\n"
            if output["success"]:
                response += f"输出:\n{output['output']}\n\n"
            else:
                response += f"错误: {output['error']}\n\n"

    elif state["intent"] == "mcp_tool_call":
        result = json.loads(state.get("mcp_result", "{}"))

        if result.get("success"):
            response = format_mcp_success_response(state["mcp_tool"], result)
        else:
            response = f"❌ MCP工具执行失败\n\n"
            response += f"工具: {state['mcp_tool']}\n"
            response += f"错误: {result.get('error', '未知错误')}"

    else:
        response = "抱歉，我无法处理这个请求。"

    print(f"[格式化响应] 完成")
    return {"response": response}


def format_mcp_success_response(tool_name: str, result: dict) -> str:
    """格式化MCP成功响应"""
    response = f"✅ MCP工具执行成功\n\n工具: {tool_name}\n\n"

    if tool_name == "fs_read":
        content = result.get("content", "")
        lines = result.get("lines", 0)
        size = result.get("size", 0)
        response += f"文件大小: {size} 字节\n"
        response += f"行数: {lines}\n\n"
        response += f"内容:\n{'-' * 60}\n{content}\n{'-' * 60}"

    elif tool_name == "fs_list":
        response += f"目录: {result.get('path', '.')}\n"
        response += f"找到 {result['total_files']} 个文件\n\n"
        for f in result["files"][:20]:
            response += f"  📄 {f['name']:<40} {f['size_human']:>10}  {f['modified']}\n"
        if result["total_files"] > 20:
            response += f"\n... 还有 {result['total_files'] - 20} 个文件"

    elif tool_name == "fs_search":
        response += f"找到 {result['total']} 个匹配文件\n\n"
        for f in result["matches"][:15]:
            response += f"  📝 {f['name']} ({f['size_human']})\n"
            if f.get("content_matched"):
                response += f"     匹配行:\n"
                for line_num, line_content in f.get("matched_lines", [])[:3]:
                    response += f"       {line_num}: {line_content.strip()[:60]}...\n"
        if result["total"] > 15:
            response += f"\n... 还有 {result['total'] - 15} 个文件"

    elif tool_name == "fs_write":
        response += f"文件路径: {result.get('path', '')}\n"
        response += f"写入大小: {result.get('size', 0)} 字节\n"
        response += f"行数: {result.get('lines', 0)}\n"
        response += f"模式: {result.get('mode', 'write')}"

    elif tool_name == "fs_info":
        response += f"文件名: {result.get('name', '')}\n"
        response += f"路径: {result.get('path', '')}\n"
        response += f"大小: {result.get('size_human', '')}\n"
        response += f"修改时间: {result.get('modified', '')}\n"
        response += f"创建时间: {result.get('created', '')}\n"
        response += f"类型: {'文件' if result.get('is_file') else '目录'}"

    elif tool_name == "get_stock_info":
        # 股票信息专门格式化
        stock_info = result.get("result", "")
        if stock_info:
            response = f"📈 股票查询结果\n\n{stock_info}"
        else:
            response += f"结果:\n{json.dumps(result, ensure_ascii=False, indent=2)}"

    elif tool_name.startswith("desktop_"):
        response += f"结果:\n{json.dumps(result.get('result', {}), ensure_ascii=False, indent=2)}"

    else:
        response += f"结果:\n{json.dumps(result, ensure_ascii=False, indent=2)}"

    return response
