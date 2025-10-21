"""
工作流节点模块
包含所有LangGraph节点函数
"""

import json
from langchain_core.messages import HumanMessage
from agent_config import AgentState, LLM_CONFIG, LLM_CONFIG2
from agent_memory import memory
from agent_utils import execute_terminal_command
from agent_llm import llm, llm_code
from mcp_manager import mcp_manager


# ============================================
# 意图分析和规划节点
# ============================================

def intent_analyzer(state: AgentState) -> dict:
    """分析用户意图（带上下文）"""
    user_input = state["user_input"]
    context = memory.get_context_string()

    prompt = f"""你是一个智能终端助手。根据用户输入和对话历史，分析用户意图。

{context}

当前用户输入: {user_input}

判断规则:
- 如果用户想读取文件、写入文件、列出目录、搜索文件、获取文件信息 -> mcp_tool_call
- 如果用户想截图、操作剪贴板、执行桌面命令 -> mcp_tool_call
- 如果用户想执行系统命令、运行程序 -> terminal_command
- 如果用户需要创建代码文件并执行、或者需要多个步骤完成任务 -> multi_step_command
- 如果用户在问问题、寻求解释、需要建议、或者引用之前的对话 -> question

只返回一个词: 'mcp_tool_call', 'terminal_command', 'multi_step_command' 或 'question'

意图:"""

    result = llm.invoke([HumanMessage(content=prompt)])
    intent = result.content.strip().lower()

    if intent not in ["mcp_tool_call", "terminal_command", "multi_step_command", "question"]:
        intent = "question"

    print(f"\n[意图分析] {user_input[:50]}...")
    print(f"           使用模型: {LLM_CONFIG['model']}")
    print(f"           意图: {intent}")

    return {"intent": intent}


def command_generator(state: AgentState) -> dict:
    """生成终端命令"""
    user_input = state["user_input"]
    recent_commands = memory.get_recent_commands()

    prompt = f"""将用户的自然语言请求转换为终端命令。

{recent_commands}

当前请求: {user_input}

示例:
- "列出当前目录的所有文件" -> ls -la
- "查看Python版本" -> python3 --version
- "显示当前路径" -> pwd

只返回命令本身，不要解释:"""

    result = llm_code.invoke([HumanMessage(content=prompt)])
    command = result.content.strip()

    print(f"[命令生成] {command}")
    print(f"           使用模型: {LLM_CONFIG2['model']}")

    return {"command": command}


def multi_step_planner(state: AgentState) -> dict:
    """多步骤规划"""
    user_input = state["user_input"]
    recent_commands = memory.get_recent_commands()

    prompt = f"""分析用户请求，返回JSON格式的执行计划。

{recent_commands}

用户请求: {user_input}

返回JSON对象:
{{
  "needs_file_creation": true/false,
  "file_path": "文件路径",
  "file_content": "文件内容",
  "commands": ["命令1", "命令2"]
}}

只返回JSON:"""

    result = llm_code.invoke([HumanMessage(content=prompt)])
    plan_text = result.content.strip()
    
    if "```json" in plan_text:
        plan_text = plan_text.split("```json")[1].split("```")[0].strip()
    elif "```" in plan_text:
        plan_text = plan_text.split("```")[1].split("```")[0].strip()
    
    try:
        plan = json.loads(plan_text)
        print(f"[多步骤规划] 使用模型: {LLM_CONFIG2['model']}")
        print(f"            需要创建文件: {plan.get('needs_file_creation', False)}")
        print(f"            命令数量: {len(plan.get('commands', []))}")
        
        return {
            "needs_file_creation": plan.get("needs_file_creation", False),
            "file_path": plan.get("file_path", ""),
            "file_content": plan.get("file_content", ""),
            "commands": plan.get("commands", [])
        }
    except json.JSONDecodeError:
        print(f"[多步骤规划] JSON解析失败")
        return {
            "needs_file_creation": False,
            "file_path": "",
            "file_content": "",
            "commands": [],
            "error": "无法解析执行计划"
        }


def mcp_tool_planner(state: AgentState) -> dict:
    """规划MCP工具调用"""
    user_input = state["user_input"]
    
    available_tools = mcp_manager.list_available_tools()
    tools_desc = "\n".join([
        f"- {t['name']}: {t['description']} (参数: {', '.join(t['params'])})"
        for t in available_tools
    ])
    
    prompt = f"""分析用户请求，选择合适的MCP工具并返回JSON格式。

可用工具:
{tools_desc}

用户请求: {user_input}

返回JSON格式:
{{
  "tool": "工具名称",
  "params": {{参数名: 参数值}}
}}

示例:
输入: "读取README.md文件"
输出: {{
  "tool": "fs_read",
  "params": {{"file_path": "README.md"}}
}}

只返回JSON:"""
    
    result = llm_code.invoke([HumanMessage(content=prompt)])
    plan_text = result.content.strip()
    
    if "```json" in plan_text:
        plan_text = plan_text.split("```json")[1].split("```")[0].strip()
    elif "```" in plan_text:
        plan_text = plan_text.split("```")[1].split("```")[0].strip()
    
    try:
        plan = json.loads(plan_text)
        print(f"[MCP工具规划] 使用模型: {LLM_CONFIG2['model']}")
        print(f"            工具: {plan.get('tool', 'unknown')}")
        print(f"            参数: {plan.get('params', {})}")
        
        return {
            "mcp_tool": plan.get("tool", ""),
            "mcp_params": plan.get("params", {})
        }
    except json.JSONDecodeError as e:
        print(f"[MCP工具规划] JSON解析失败: {e}")
        return {
            "mcp_tool": "",
            "mcp_params": {},
            "error": "无法解析MCP工具规划"
        }


def question_answerer(state: AgentState) -> dict:
    """回答用户问题"""
    user_input = state["user_input"]
    context = memory.get_context_string()
    recent_commands = memory.get_recent_commands()

    prompt = f"""你是一个友好的AI终端助手。回答用户问题，并利用对话历史提供更好的帮助。

{context}

{recent_commands}

当前问题: {user_input}

请简洁但全面地回答用户的问题。如果用户提到"刚才"、"之前"等词，请参考对话历史。

回答:"""

    result = llm.invoke([HumanMessage(content=prompt)])
    response = result.content

    print(f"[问题回答] 生成回答")
    print(f"           使用模型: {LLM_CONFIG['model']}")

    return {"response": response}


# ============================================
# 执行节点
# ============================================

def file_creator(state: AgentState) -> dict:
    """创建文件"""
    file_path = state["file_path"]
    file_content = state["file_content"]
    
    print(f"[文件创建] 创建文件: {file_path}")
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
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
        return {
            "command_output": result["output"],
            "error": ""
        }
    else:
        print(f"[执行失败] {result['error']}")
        return {
            "command_output": "",
            "error": result["error"]
        }


def multi_command_executor(state: AgentState) -> dict:
    """执行多个终端命令"""
    commands = state["commands"]
    outputs = []
    
    print(f"[多命令执行] 共{len(commands)}个命令")
    
    for idx, command in enumerate(commands, 1):
        print(f"[多命令执行] 执行第{idx}个命令: {command}")
        result = execute_terminal_command(command)
        
        outputs.append({
            "command": command,
            "success": result["success"],
            "output": result["output"],
            "error": result["error"]
        })
        
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


# ============================================
# 响应格式化节点
# ============================================

def response_formatter(state: AgentState) -> dict:
    """格式化最终响应"""
    if state["intent"] == "terminal_command":
        if state.get("error"):
            response = f"❌ 命令执行失败\n\n命令: {state['command']}\n错误: {state['error']}"
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
            response = format_mcp_success_response(state['mcp_tool'], result)
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
        content = result.get('content', '')
        lines = result.get('lines', 0)
        size = result.get('size', 0)
        response += f"文件大小: {size} 字节\n"
        response += f"行数: {lines}\n\n"
        response += f"内容:\n{'-' * 60}\n{content}\n{'-' * 60}"
    
    elif tool_name == "fs_list":
        response += f"目录: {result.get('path', '.')}\n"
        response += f"找到 {result['total_files']} 个文件\n\n"
        for f in result['files'][:20]:
            response += f"  📄 {f['name']:<40} {f['size_human']:>10}  {f['modified']}\n"
        if result['total_files'] > 20:
            response += f"\n... 还有 {result['total_files'] - 20} 个文件"
    
    elif tool_name == "fs_search":
        response += f"找到 {result['total']} 个匹配文件\n\n"
        for f in result['matches'][:15]:
            response += f"  📝 {f['name']} ({f['size_human']})\n"
            if f.get('content_matched'):
                response += f"     匹配行:\n"
                for line_num, line_content in f.get('matched_lines', [])[:3]:
                    response += f"       {line_num}: {line_content.strip()[:60]}...\n"
        if result['total'] > 15:
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
    
    elif tool_name.startswith("desktop_"):
        response += f"结果:\n{json.dumps(result.get('result', {}), ensure_ascii=False, indent=2)}"
    
    else:
        response += f"结果:\n{json.dumps(result, ensure_ascii=False, indent=2)}"
    
    return response
