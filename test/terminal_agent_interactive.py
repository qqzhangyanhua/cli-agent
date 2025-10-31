"""
AI智能体终端控制工具 - 交互式版本 + MCP集成
支持对话功能、记忆功能和MCP工具集成

功能:
- 文件系统访问（读/写/列表/搜索）
- 桌面控制（desktop-commander）
- 终端命令执行
- 智能对话和记忆

运行: python3 terminal_agent_interactive.py
"""

import subprocess
import json
from typing import TypedDict, Literal, List
from datetime import datetime
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from mcp_manager import mcp_manager  # MCP管理器

# ============================================
# 配置区
# ============================================
# 通用LLM配置 - 用于意图分析、问答等
LLM_CONFIG = {
    "model": "kimi-k2-0905-preview",
    "base_url": "https://api.moonshot.cn/v1",
    "api_key": "sk-",
    "temperature": 0,
}

# 代码生成专用LLM配置 - 用于生成命令和代码
LLM_CONFIG2 = {
    "model": "claude-3-5-sonnet",  # 使用Claude作为代码生成模型
    "base_url": "https://sdwfger.edu.kg/v1",
    "api_key": "sk-",
    "temperature": 0,
}


# ============================================
# 数据结构定义
# ============================================
class AgentState(TypedDict):
    """智能体状态"""
    user_input: str
    intent: Literal["terminal_command", "multi_step_command", "mcp_tool_call", "question", "unknown"]
    command: str
    commands: list
    command_output: str
    command_outputs: list
    response: str
    error: str
    needs_file_creation: bool
    file_path: str
    file_content: str
    chat_history: list  # 对话历史记忆
    # MCP相关字段
    mcp_tool: str  # MCP工具名称
    mcp_params: dict  # MCP工具参数
    mcp_result: str  # MCP执行结果


class ConversationMemory:
    """对话记忆管理"""
    def __init__(self, max_history=10):
        self.history: List[dict] = []
        self.max_history = max_history
        self.command_history: List[dict] = []  # 命令执行历史
    
    def add_interaction(self, user_input: str, agent_response: str, intent: str):
        """添加一次交互到历史"""
        self.history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": user_input,
            "agent": agent_response,
            "intent": intent
        })
        
        # 保持历史记录在限制范围内
        if len(self.history) > self.max_history:
            self.history.pop(0)
    
    def add_command(self, command: str, output: str, success: bool):
        """记录命令执行历史"""
        self.command_history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "command": command,
            "output": output,
            "success": success
        })
        
        if len(self.command_history) > 20:
            self.command_history.pop(0)
    
    def get_context_string(self) -> str:
        """获取对话上下文字符串"""
        if not self.history:
            return "这是我们的第一次对话。"
        
        context = "对话历史:\n"
        for idx, interaction in enumerate(self.history[-5:], 1):  # 只取最近5条
            context += f"{idx}. 用户: {interaction['user']}\n"
            context += f"   助手: {interaction['agent'][:100]}...\n"  # 截断长响应
        
        return context
    
    def get_recent_commands(self, n=3) -> str:
        """获取最近的命令历史"""
        if not self.command_history:
            return "暂无命令执行历史。"
        
        recent = self.command_history[-n:]
        result = "最近执行的命令:\n"
        for cmd in recent:
            status = "✅" if cmd["success"] else "❌"
            result += f"{status} {cmd['command']}\n"
        
        return result
    
    def clear(self):
        """清空记忆"""
        self.history.clear()
        self.command_history.clear()


# ============================================
# 全局记忆实例
# ============================================
memory = ConversationMemory(max_history=10)


# ============================================
# 初始化 LLM
# ============================================
# 通用LLM - 用于意图分析、问答等
llm = ChatOpenAI(
    model=LLM_CONFIG["model"],
    base_url=LLM_CONFIG["base_url"],
    api_key=LLM_CONFIG["api_key"],
    temperature=LLM_CONFIG["temperature"],
    default_headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
)

# 代码生成专用LLM - 用于生成命令和代码
llm_code = ChatOpenAI(
    model=LLM_CONFIG2["model"],
    base_url=LLM_CONFIG2["base_url"],
    api_key=LLM_CONFIG2["api_key"],
    temperature=LLM_CONFIG2["temperature"],
    default_headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
)


# ============================================
# 工具函数 - 终端命令执行
# ============================================

def execute_terminal_command(command: str) -> dict:
    """安全地执行终端命令"""
    dangerous_commands = ["rm -rf", "sudo rm", "chmod 777", "format", "del /f"]
    for dangerous in dangerous_commands:
        if dangerous in command.lower():
            return {
                "success": False,
                "output": "",
                "error": f"⚠️ 拒绝执行危险命令: {command}"
            }

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
            cwd="/Users/zhangyanhua/Desktop/AI/tushare/quantification/example"
        )
        
        output = result.stdout if result.stdout else "(命令执行成功，无输出)"
        
        # 记录到命令历史
        memory.add_command(command, output, result.returncode == 0)
        
        return {
            "success": result.returncode == 0,
            "output": output,
            "error": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": "⏱️ 命令执行超时(>10秒)"
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": f"❌ 执行失败: {str(e)}"
        }


# ============================================
# 节点函数定义
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
        intent = "question"  # 默认为问答

    print(f"\n[意图分析] {user_input[:50]}...")
    print(f"           使用模型: {LLM_CONFIG['model']}")
    print(f"           意图: {intent}")

    return {"intent": intent}


def command_generator(state: AgentState) -> dict:
    """生成终端命令（带上下文）"""
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

    result = llm_code.invoke([HumanMessage(content=prompt)])  # 使用代码生成LLM
    command = result.content.strip()

    print(f"[命令生成] {command}")
    print(f"           使用模型: {LLM_CONFIG2['model']}")

    return {"command": command}


def multi_step_planner(state: AgentState) -> dict:
    """多步骤规划（带上下文）"""
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

示例:
输入: "创建一个Python文件test.py，打印1到10，然后执行"
输出:
{{
  "needs_file_creation": true,
  "file_path": "test.py",
  "file_content": "for i in range(1, 11):\\n    print(i)",
  "commands": ["python3 test.py"]
}}

只返回JSON:"""

    result = llm_code.invoke([HumanMessage(content=prompt)])  # 使用代码生成LLM
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


def mcp_tool_planner(state: AgentState) -> dict:
    """规划MCP工具调用"""
    user_input = state["user_input"]
    
    # 获取可用工具列表
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

输入: "列出当前目录的所有Python文件"
输出: {{
  "tool": "fs_list",
  "params": {{"dir_path": ".", "pattern": "*.py"}}
}}

输入: "搜索包含LLM_CONFIG的Python文件"
输出: {{
  "tool": "fs_search",
  "params": {{"dir_path": ".", "filename_pattern": "*.py", "content_search": "LLM_CONFIG"}}
}}

只返回JSON:"""
    
    result = llm_code.invoke([HumanMessage(content=prompt)])
    plan_text = result.content.strip()
    
    # 提取JSON
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
            response = f"✅ MCP工具执行成功\n\n"
            response += f"工具: {state['mcp_tool']}\n\n"
            
            # 根据不同工具类型格式化输出
            if state['mcp_tool'] == "fs_read":
                content = result.get('content', '')
                lines = result.get('lines', 0)
                size = result.get('size', 0)
                response += f"文件大小: {size} 字节\n"
                response += f"行数: {lines}\n\n"
                response += f"内容:\n{'-' * 60}\n{content}\n{'-' * 60}"
            
            elif state['mcp_tool'] == "fs_list":
                response += f"目录: {result.get('path', '.')}\n"
                response += f"找到 {result['total_files']} 个文件\n\n"
                for f in result['files'][:20]:
                    response += f"  📄 {f['name']:<40} {f['size_human']:>10}  {f['modified']}\n"
                if result['total_files'] > 20:
                    response += f"\n... 还有 {result['total_files'] - 20} 个文件"
            
            elif state['mcp_tool'] == "fs_search":
                response += f"找到 {result['total']} 个匹配文件\n\n"
                for f in result['matches'][:15]:
                    response += f"  📝 {f['name']} ({f['size_human']})\n"
                    if f.get('content_matched'):
                        response += f"     匹配行:\n"
                        for line_num, line_content in f.get('matched_lines', [])[:3]:
                            response += f"       {line_num}: {line_content.strip()[:60]}...\n"
                if result['total'] > 15:
                    response += f"\n... 还有 {result['total'] - 15} 个文件"
            
            elif state['mcp_tool'] == "fs_write":
                response += f"文件路径: {result.get('path', '')}\n"
                response += f"写入大小: {result.get('size', 0)} 字节\n"
                response += f"行数: {result.get('lines', 0)}\n"
                response += f"模式: {result.get('mode', 'write')}"
            
            elif state['mcp_tool'] == "fs_info":
                response += f"文件名: {result.get('name', '')}\n"
                response += f"路径: {result.get('path', '')}\n"
                response += f"大小: {result.get('size_human', '')}\n"
                response += f"修改时间: {result.get('modified', '')}\n"
                response += f"创建时间: {result.get('created', '')}\n"
                response += f"类型: {'文件' if result.get('is_file') else '目录'}"
            
            elif state['mcp_tool'].startswith("desktop_"):
                # 桌面控制工具结果
                response += f"结果:\n{json.dumps(result.get('result', {}), ensure_ascii=False, indent=2)}"
            
            else:
                response += f"结果:\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        else:
            response = f"❌ MCP工具执行失败\n\n"
            response += f"工具: {state['mcp_tool']}\n"
            response += f"错误: {result.get('error', '未知错误')}"
    
    else:
        response = "抱歉，我无法处理这个请求。"

    print(f"[格式化响应] 完成")

    return {"response": response}


def question_answerer(state: AgentState) -> dict:
    """回答用户问题（带上下文和记忆）"""
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
    workflow.add_node("plan_mcp_tool", mcp_tool_planner)  # MCP工具规划
    workflow.add_node("execute_mcp_tool", mcp_tool_executor)  # MCP工具执行
    workflow.add_node("format_response", response_formatter)
    workflow.add_node("answer_question", question_answerer)

    workflow.set_entry_point("analyze_intent")

    # 意图路由
    workflow.add_conditional_edges(
        "analyze_intent",
        route_by_intent,
        {
            "generate_command": "generate_command",
            "plan_steps": "plan_steps",
            "plan_mcp_tool": "plan_mcp_tool",  # MCP工具路径
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


# ============================================
# 交互式主函数
# ============================================

def print_header():
    """打印欢迎信息"""
    print("\n" + "=" * 80)
    print("🤖 AI智能终端助手 - 交互式版本 + MCP集成")
    print("=" * 80)
    print("\n✨ 功能:")
    print("  • 自然语言执行终端命令")
    print("  • 创建和执行代码文件")
    print("  • 智能问答")
    print("  • 对话记忆（记住上下文）")
    print("\n🔌 MCP功能:")
    print("  • 文件系统: 读取/写入/列出/搜索文件")
    print("  • 桌面控制: 截图/剪贴板/执行命令")
    
    # 显示可用工具数量
    tools = mcp_manager.list_available_tools()
    fs_tools = [t for t in tools if t['type'] == 'filesystem']
    desktop_tools = [t for t in tools if t['type'] == 'desktop-commander']
    print(f"  • 已加载: {len(fs_tools)}个文件工具, {len(desktop_tools)}个桌面工具")
    
    print("\n🔧 双LLM配置:")
    print(f"  • 通用模型: {LLM_CONFIG['model']} (意图分析、问答)")
    print(f"  • 代码模型: {LLM_CONFIG2['model']} (命令生成、代码编写)")
    print("\n💡 特殊命令:")
    print("  • 'exit' 或 'quit' - 退出程序")
    print("  • 'clear' - 清空对话历史")
    print("  • 'history' - 查看对话历史")
    print("  • 'commands' - 查看命令执行历史")
    print("  • 'models' - 查看当前模型配置")
    print("  • 'tools' - 查看MCP工具列表")
    print("\n" + "=" * 80 + "\n")


def handle_special_commands(user_input: str) -> bool:
    """处理特殊命令，返回True表示已处理"""
    user_input_lower = user_input.lower().strip()
    
    if user_input_lower in ['exit', 'quit', '退出']:
        print("\n👋 再见！感谢使用AI智能终端助手！\n")
        return True
    
    if user_input_lower in ['clear', '清空']:
        memory.clear()
        print("\n✅ 对话历史已清空\n")
        return False
    
    if user_input_lower in ['history', '历史']:
        if not memory.history:
            print("\n暂无对话历史\n")
        else:
            print("\n📜 对话历史:")
            print("─" * 80)
            for idx, interaction in enumerate(memory.history, 1):
                print(f"\n[{interaction['timestamp']}]")
                print(f"👤 用户: {interaction['user']}")
                print(f"🤖 助手: {interaction['agent'][:200]}...")
                print(f"   (意图: {interaction['intent']})")
            print("─" * 80 + "\n")
        return False
    
    if user_input_lower in ['commands', '命令']:
        if not memory.command_history:
            print("\n暂无命令执行历史\n")
        else:
            print("\n📋 命令执行历史:")
            print("─" * 80)
            for cmd in memory.command_history:
                status = "✅" if cmd["success"] else "❌"
                print(f"{status} [{cmd['timestamp']}] {cmd['command']}")
            print("─" * 80 + "\n")
        return False
    
    if user_input_lower in ['models', '模型']:
        print("\n🔧 当前模型配置:")
        print("─" * 80)
        print("\n📌 通用模型 (LLM_CONFIG):")
        print(f"   模型: {LLM_CONFIG['model']}")
        print(f"   API: {LLM_CONFIG['base_url']}")
        print(f"   用途: 意图分析、智能问答、上下文理解")
        print(f"   使用场景: intent_analyzer(), question_answerer()")
        
        print("\n📌 代码生成模型 (LLM_CONFIG2):")
        print(f"   模型: {LLM_CONFIG2['model']}")
        print(f"   API: {LLM_CONFIG2['base_url']}")
        print(f"   用途: 命令生成、代码编写、任务规划")
        print(f"   使用场景: command_generator(), multi_step_planner(), mcp_tool_planner()")
        
        print("\n💡 提示:")
        print("   - 不同任务使用最适合的模型")
        print("   - 代码生成任务使用专业的代码模型")
        print("   - 对话和理解任务使用通用模型")
        print("─" * 80 + "\n")
        return False
    
    if user_input_lower in ['tools', '工具']:
        print("\n🛠️ 可用的MCP工具:")
        print("─" * 80)
        tools = mcp_manager.list_available_tools()
        
        for tool_type in ['filesystem', 'desktop-commander']:
            type_tools = [t for t in tools if t['type'] == tool_type]
            if type_tools:
                icon = "📁" if tool_type == "filesystem" else "🖥️"
                print(f"\n{icon} {tool_type} ({len(type_tools)}个):")
                for t in type_tools:
                    params_str = ", ".join(t['params'][:3])
                    if len(t['params']) > 3:
                        params_str += "..."
                    print(f"   • {t['name']:25} - {t['description']}")
                    print(f"     参数: {params_str}")
        
        print("\n💡 使用示例:")
        print("   • '读取README.md文件'")
        print("   • '列出当前目录的所有Python文件'")
        print("   • '搜索包含LLM_CONFIG的文件'")
        print("   • '写入内容到test.txt文件'")
        print("─" * 80 + "\n")
        return False
    
    return None


def main():
    """交互式主循环"""
    
    print_header()
    
    agent = build_agent()
    
    print("🎬 准备就绪！请输入你的指令或问题...\n")
    
    while True:
        try:
            # 获取用户输入
            user_input = input("👤 你: ").strip()
            
            if not user_input:
                continue
            
            # 处理特殊命令
            special_result = handle_special_commands(user_input)
            if special_result is True:  # 退出
                break
            elif special_result is False:  # 已处理，继续循环
                continue
            
            print()  # 空行
            
            # 构建初始状态
            initial_state: AgentState = {
                "user_input": user_input,
                "intent": "unknown",
                "command": "",
                "commands": [],
                "command_output": "",
                "command_outputs": [],
                "response": "",
                "error": "",
                "needs_file_creation": False,
                "file_path": "",
                "file_content": "",
                "chat_history": [],
                # MCP相关字段
                "mcp_tool": "",
                "mcp_params": {},
                "mcp_result": ""
            }
            
            # 执行工作流
            result = agent.invoke(initial_state)
            
            # 显示响应
            print("─" * 80)
            print(f"🤖 助手: {result['response']}")
            print("─" * 80 + "\n")
            
            # 保存到记忆
            memory.add_interaction(
                user_input, 
                result['response'], 
                result.get('intent', 'unknown')
            )
            
        except KeyboardInterrupt:
            print("\n\n👋 检测到中断信号，退出程序...\n")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {str(e)}\n")
            print("请重试或输入 'exit' 退出\n")


if __name__ == "__main__":
    main()
