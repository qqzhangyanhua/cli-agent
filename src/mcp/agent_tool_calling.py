"""
智能工具调用节点 - 利用 LangChain 的 Tool Calling 能力
让 LLM 自主决定调用哪个工具
"""

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.prebuilt import create_react_agent
from datetime import datetime
import json

from src.core.agent_config import AgentState
from src.core.agent_llm import llm
from src.tools.todo_tools import todo_tools, add_todo_tool, query_todo_tool
from src.tools.git_commit_tools import generate_commit_tool
from src.tools.code_review_tools import code_review_tool
from src.tools.auto_commit_tools import auto_commit_tool, git_pull_tool, git_push_tool
from src.tools.project_manager_tools import project_manager_tools, start_project_tool, build_project_tool, diagnose_project_tool, stop_project_tool
from src.tools.daily_report_tools import daily_report_tools, generate_daily_report_tool
from src.core.json_utils import extract_json_str, safe_json_loads
from src.core.logger import get_logger, log_json_event

_log = get_logger("tool-agent")


def create_tool_agent():
    """创建一个支持工具调用的 ReAct 代理"""

    system_prompt = f"""你是一个智能终端助手，可以帮助用户管理待办事项、Git操作和项目管理。

今天的日期是: {datetime.now().strftime("%Y-%m-%d %A")}

当用户提到相对日期时，请转换为具体日期：
- 今天 = {datetime.now().strftime("%Y-%m-%d")}
- 明天 = {(datetime.now() + __import__('datetime').timedelta(days=1)).strftime("%Y-%m-%d")}
- 后天 = {(datetime.now() + __import__('datetime').timedelta(days=2)).strftime("%Y-%m-%d")}

你有以下工具可以使用：

📝 待办管理:
1. add_todo - 添加待办事项
2. query_todo - 查询待办事项

🔧 Git操作:
3. generate_commit - 生成Git commit消息
4. code_review - 代码审查
5. auto_commit - 自动Git提交（add + commit）
6. git_pull - 拉取远程代码
7. git_push - 推送代码到远程

🚀 项目管理:
8. start_project - 智能启动项目（自动检测类型、安装依赖）
9. build_project - 智能打包项目

📊 日报助手:
10. generate_daily_report - 生成日报（汇总当天Git提交、命令、交互记录）

请根据用户的输入，判断用户意图并调用合适的工具。

重要规则：
- 待办事项: "今天18点给XX打电话" → add_todo, "今天有什么要做的" → query_todo
- 项目管理: "启动项目"/"运行项目" → start_project, "打包项目"/"构建项目" → build_project
- Git操作: "提交代码" → auto_commit, "生成commit消息" → generate_commit
- 日报生成: "生成日报"/"今日总结"/"工作报告" → generate_daily_report
- 一定要将相对日期转换为具体的 YYYY-MM-DD 格式
- 工具调用的输入必须是合法的 JSON 字符串
"""

    # 创建 ReAct 代理（LangGraph内置的工具调用代理）
    agent = create_react_agent(
        llm,
        tools=todo_tools,
        state_modifier=system_prompt
    )

    return agent


def tool_calling_node(state: AgentState) -> dict:
    """
    智能工具调用节点
    使用 LangChain 的 ReAct 模式让 LLM 自主选择和调用工具
    """
    user_input = state["user_input"]

    print(f"\n[智能代理] 分析用户意图并选择工具...")

    # 创建工具代理
    agent = create_tool_agent()

    # 调用代理
    try:
        result = agent.invoke({
            "messages": [HumanMessage(content=user_input)]
        })

        # 提取最终响应
        messages = result.get("messages", [])

        # 获取最后一条AI消息
        final_response = ""
        tool_calls_made = []

        for msg in messages:
            if isinstance(msg, AIMessage):
                # 检查是否有工具调用
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        tool_calls_made.append({
                            "tool": tool_call.get("name", "unknown"),
                            "args": tool_call.get("args", {})
                        })
                # 如果有文本内容，作为候选响应
                if msg.content:
                    final_response = msg.content

            elif isinstance(msg, ToolMessage):
                # 工具调用的结果
                final_response = msg.content

        print(f"[智能代理] ✅ 完成")
        if tool_calls_made:
            print(f"[智能代理] 调用的工具: {[t['tool'] for t in tool_calls_made]}")

        # 判断意图
        if any(t['tool'] == 'add_todo' for t in tool_calls_made):
            intent = "add_todo"
        elif any(t['tool'] == 'query_todo' for t in tool_calls_made):
            intent = "query_todo"
        elif any(t['tool'] == 'generate_daily_report' for t in tool_calls_made):
            intent = "daily_report"
        else:
            intent = "question"  # 可能是普通问答

        return {
            "intent": intent,
            "response": final_response if final_response else "处理完成"
        }

    except Exception as e:
        print(f"[智能代理] ❌ 错误: {str(e)}")
        return {
            "intent": "error",
            "response": f"❌ 处理请求时发生错误: {str(e)}",
            "error": str(e)
        }


def _get_all_available_tools() -> list:
    """
    获取所有可用工具（MCP + LangChain）
    
    Returns:
        工具列表，每个工具包含 name, description, params 等信息
    """
    from src.mcp.mcp_manager import mcp_manager
    
    # 1. 获取 MCP 工具
    mcp_tools = mcp_manager.list_available_tools()
    
    # 2. 添加 LangChain 工具
    langchain_tools_info = [
        {
            "name": "add_todo",
            "description": "添加待办事项。当用户想要记录、添加、设置一个待办或提醒时使用。",
            "params": ["date", "time", "content"]
        },
        {
            "name": "query_todo", 
            "description": "查询待办事项。当用户想要查看、询问待办事项时使用。",
            "params": ["type", "date", "keyword"]
        },
        {
            "name": "generate_commit",
            "description": "生成Git commit消息。分析代码变更并生成符合规范的commit消息。",
            "params": []
        },
        {
            "name": "auto_commit",
            "description": "自动Git提交。执行 git add + commit 流程。",
            "params": []
        },
        {
            "name": "git_pull",
            "description": "拉取远程代码。执行 git pull 操作。",
            "params": []
        },
        {
            "name": "git_push", 
            "description": "推送代码到远程。执行 git push 操作。",
            "params": []
        },
        {
            "name": "code_review",
            "description": "代码审查。分析代码变更并提供审查意见。",
            "params": []
        },
        {
            "name": "start_project",
            "description": "智能启动项目。自动检测项目类型（Node.js/Python），分析启动命令，后台执行并监控输出，自动处理依赖缺失问题。",
            "params": ["work_dir"]
        },
        {
            "name": "build_project",
            "description": "智能打包项目。自动检测项目类型，分析打包命令并执行。",
            "params": ["work_dir"]
        },
        {
            "name": "diagnose_project",
            "description": "诊断项目运行状态。检查进程、端口、连接等状态，提供详细的诊断报告。",
            "params": ["pid", "port"]
        },
        {
            "name": "stop_project",
            "description": "停止运行中的项目。可以停止开发服务器、构建进程等。",
            "params": ["port", "pid"]
        },
        {
            "name": "environment_diagnostic",
            "description": "诊断开发环境配置。检查Python版本、Node.js、依赖包、开发工具等环境状态，提供详细的环境诊断报告。",
            "params": []
        },
        {
            "name": "generate_daily_report",
            "description": "生成日报。汇总当天的Git提交、命令执行、AI交互等活动，自动生成工作日报。当用户说'生成日报'、'今日总结'、'工作报告'时使用。",
            "params": ["work_dir", "template", "save_file"]
        }
    ]
    
    # 合并所有工具
    all_tools = mcp_tools + langchain_tools_info
    
    return all_tools


def _generate_tools_documentation(tools: list) -> str:
    """
    自动生成工具文档

    Args:
        tools: 工具列表

    Returns:
        格式化的工具文档字符串
    """
    doc_lines = ["可用工具:"]

    for i, tool in enumerate(tools, 1):
        params = tool.get("parameters", {}).get("properties", {})
        required = tool.get("parameters", {}).get("required", [])

        # 构建参数说明
        param_parts = []
        for param_name, param_schema in params.items():
            param_type = param_schema.get("type", "any")
            param_desc = param_schema.get("description", "")
            is_required = " (必填)" if param_name in required else " (可选)"
            param_parts.append(f"{param_name} ({param_type}{is_required}): {param_desc}")

        params_str = "\n   ".join(param_parts) if param_parts else "无"

        doc_lines.append(
            f"{i}. {tool['name']} - {tool['description']}\n"
            f"   参数: {params_str}"
        )

    doc_lines.append(f"\n{len(tools) + 1}. none - 不需要工具（普通问答）")

    return "\n\n".join(doc_lines)


def _infer_intent_from_tool(tool_name: str) -> str:
    """
    根据工具名推断意图

    Args:
        tool_name: 工具名称

    Returns:
        意图标识
    """
    # 工具名到意图的映射（用于需要特殊处理的工具）
    intent_map = {
        "add_todo": "add_todo",
        "query_todo": "query_todo",
        "generate_commit": "git_commit",
        "auto_commit": "auto_commit",
        "full_git_workflow": "full_git_workflow",
        "git_pull": "git_pull",
        "git_push": "git_push",
        "code_review": "code_review",
        "data_conversion": "data_conversion",
        "environment_diagnostic": "environment_diagnostic",
        "terminal_command": "terminal_command",
        "start_project": "start_project",
        "build_project": "build_project",
        "diagnose_project": "diagnose_project",
        "stop_project": "stop_project",
        "generate_daily_report": "daily_report",
    }

    # 如果在映射表中，返回对应意图
    if tool_name in intent_map:
        return intent_map[tool_name]

    # 否则，根据工具类型判断
    # MCP工具统一返回 mcp_tool_call
    return "mcp_tool_call"


def _call_langchain_tool(tool_name: str, tool_args: dict) -> str:
    """
    调用 LangChain Tool（用于待办、Git等已封装的工具）

    Args:
        tool_name: 工具名称
        tool_args: 工具参数

    Returns:
        工具执行结果
    """
    # LangChain 工具映射
    langchain_tools = {
        "add_todo": add_todo_tool,
        "query_todo": query_todo_tool,
        "generate_commit": generate_commit_tool,
        "auto_commit": auto_commit_tool,
        "git_pull": git_pull_tool,
        "git_push": git_push_tool,
        "code_review": code_review_tool,
        "start_project": start_project_tool,
        "build_project": build_project_tool,
        "diagnose_project": diagnose_project_tool,
        "stop_project": stop_project_tool,
        "generate_daily_report": generate_daily_report_tool,
    }

    if tool_name in langchain_tools:
        tool = langchain_tools[tool_name]
        # LangChain Tool 需要 JSON 字符串作为输入
        payload = json.dumps(tool_args, ensure_ascii=False) if tool_args else ""
        result_text = tool.func(payload)
        try:
            log_json_event(_log, "tool_call", {
                "tool": tool_name,
                "tool_type": "langchain",
                "success": True,
            })
        except Exception:
            pass
        return result_text

    try:
        log_json_event(_log, "tool_call", {"tool": tool_name, "tool_type": "langchain", "success": False, "error": "unknown_tool"}, level="error")
    except Exception:
        pass
    return f"❌ 未知的 LangChain 工具: {tool_name}"


def extract_json(text: str) -> str:
    """兼容旧名，委托到健壮实现"""
    return extract_json_str(text)


def _format_mcp_tool_result(tool_name: str, mcp_result: dict) -> str:
    """
    格式化 MCP 工具结果
    
    Args:
        tool_name: 工具名称
        mcp_result: MCP 工具调用结果
    
    Returns:
        格式化后的响应字符串
    """
    # 对于内置工具，mcp_result 本身就是结果
    # 对于 MCP 工具，mcp_result 包含 result 字段
    if "result" in mcp_result:
        result = mcp_result.get("result", {})
    else:
        result = mcp_result
    
    if tool_name == "fs_list":
        # 格式化文件列表结果
        if isinstance(result, dict):
            total_files = result.get("total_files", 0)
            files = result.get("files", [])
            path = result.get("path", ".")
            pattern = result.get("pattern", "*")
            
            response = f"✅ 文件列表查询成功\n\n"
            response += f"📂 目录: {path}\n"
            response += f"🔍 模式: {pattern}\n"
            response += f"📊 找到 {total_files} 个文件\n\n"
            
            if files:
                response += "文件列表:\n"
                response += "─" * 80 + "\n"
                for f in files[:20]:  # 最多显示20个文件
                    response += f"📄 {f.get('name', '')}\n"
                    if f.get('size_human'):
                        response += f"   大小: {f['size_human']}\n"
                    if f.get('modified'):
                        response += f"   修改: {f['modified']}\n"
                    response += "\n"
                
                if total_files > 20:
                    response += f"... 还有 {total_files - 20} 个文件\n"
                
                response += "─" * 80
            else:
                response += "📭 没有找到匹配的文件"
            
            return response
        else:
            return f"✅ 工具执行成功\n\n结果: {result}"
    
    elif tool_name == "fs_read":
        # 格式化文件读取结果
        if isinstance(result, dict):
            content = result.get("content", "")
            size = result.get("size", 0)
            lines = result.get("lines", 0)
            path = result.get("path", "")
            
            response = f"✅ 文件读取成功\n\n"
            response += f"📄 文件: {path}\n"
            response += f"📊 大小: {size} 字节\n"
            response += f"📏 行数: {lines}\n\n"
            response += "内容:\n"
            response += "─" * 80 + "\n"
            
            # 限制输出长度
            if len(content) > 2000:
                response += content[:2000] + "\n\n... (内容太长，已截断)\n"
            else:
                response += content + "\n"
            
            response += "─" * 80
            return response
        else:
            return f"✅ 文件读取成功\n\n内容:\n{result}"
    
    elif tool_name == "fs_search":
        # 格式化文件搜索结果
        if isinstance(result, dict):
            total = result.get("total", 0)
            matches = result.get("matches", [])
            
            response = f"✅ 文件搜索完成\n\n"
            response += f"🔍 找到 {total} 个匹配文件\n\n"
            
            if matches:
                response += "匹配结果:\n"
                response += "─" * 80 + "\n"
                for match in matches[:15]:  # 最多显示15个结果
                    response += f"📝 {match.get('name', '')}\n"
                    if match.get('size_human'):
                        response += f"   大小: {match['size_human']}\n"
                    if match.get('content_matched'):
                        response += f"   内容匹配: 是\n"
                    response += "\n"
                
                if total > 15:
                    response += f"... 还有 {total - 15} 个结果\n"
                
                response += "─" * 80
            else:
                response += "📭 没有找到匹配的文件"
            
            return response
        else:
            return f"✅ 搜索完成\n\n结果: {result}"
    
    else:
        # 其他工具，简单格式化
        if isinstance(result, dict):
            return f"✅ {tool_name} 执行成功\n\n结果:\n{json.dumps(result, ensure_ascii=False, indent=2)}"
        else:
            return f"✅ {tool_name} 执行成功\n\n结果: {result}"


def simple_tool_calling_node(state: dict, enable_streaming: bool = True) -> dict:
    """
    简化版工具调用节点 - 动态工具列表，零硬编码
    使用 LLM 选择工具，然后自动分发调用

    Args:
        state: 当前状态（字典格式）
        enable_streaming: 是否启用流式输出（问答时使用）
    """
    from src.mcp.mcp_manager import mcp_manager

    user_input = state.get("user_input", "")

    print(f"\n[工具选择] 分析用户意图...")

    # 动态获取所有可用工具（MCP + LangChain）
    available_tools = _get_all_available_tools()

    # 自动生成工具文档
    tools_doc = _generate_tools_documentation(available_tools)

    # 先检查是否是打开目录的请求
    user_input_lower = user_input.lower()
    open_keywords = ["打开", "open"]
    directory_keywords = ["目录", "文件夹", "终端", "directory", "folder", "finder", "explorer", "文件管理器", "资源管理器"]
    
    has_open = any(kw in user_input_lower for kw in open_keywords)
    has_directory = any(kw in user_input_lower for kw in directory_keywords)
    
    # 如果是打开目录请求，直接返回terminal_command意图
    if has_open and has_directory:
        print(f"[工具选择] 识别为打开目录请求，转为terminal_command")
        return {
            "intent": "terminal_command",
            "response": ""  # 让后续的command_generator处理
        }

    # 让 LLM 选择工具和参数
    prompt = f"""你是一个工具选择助手。根据用户输入，选择合适的工具并提取参数。

今天是: {datetime.now().strftime("%Y-%m-%d")}

{tools_doc}

用户输入: {user_input}

请返回 JSON 格式:
{{
    "tool": "工具名称",
    "args": {{参数字典}}
}}

只返回 JSON，不要其他内容。

注意：
- 将相对日期（今天、明天等）转换为具体日期
- 如果是打开目录/文件夹的请求，返回 {{"tool": "none", "args": {{}}}}
- 如果无法判断，返回 {{"tool": "none", "args": {{}}}}
"""

    try:
        result = llm.invoke([HumanMessage(content=prompt)])
        response_text = result.content.strip()

        # 提取 JSON
        response_text = extract_json(response_text)
        obj, err = safe_json_loads(response_text)
        if err:
            raise json.JSONDecodeError(err, response_text, 0)
        tool_choice = obj

        tool_name = tool_choice.get("tool", "none")
        tool_args = tool_choice.get("args", {})

        # 诊断端口兜底：当选择了 diagnose_project 但未提取到端口参数时，
        # 从原始用户输入中尝试解析端口号，提升健壮性（示例：“查看3000端口调用情况”）
        if tool_name == "diagnose_project":
            try:
                if not tool_args or not tool_args.get("port"):
                    import re
                    # 优先匹配 “端口 3000” 或 “端口:3000/端口：3000”
                    m = re.search(r"(?:端口|port)\s*[：:]?\s*(\d{2,5})", user_input, re.IGNORECASE)
                    if not m:
                        # 匹配 “3000端口”
                        m = re.search(r"\b(\d{2,5})\b\s*端口", user_input)
                    if not m:
                        # 匹配 “localhost:3000”
                        m = re.search(r"localhost\s*[:：]\s*(\d{2,5})", user_input, re.IGNORECASE)
                    if m:
                        tool_args = dict(tool_args or {})
                        tool_args["port"] = m.group(1)
            except Exception:
                pass

        print(f"[工具选择] 选择工具: {tool_name}")
        if tool_args:
            print(f"[工具选择] 参数: {tool_args}")

        # 如果不需要工具，返回问答意图
        if tool_name == "none":
            return {
                "intent": "question",
                "response": ""  # 需要后续节点生成回答
            }

        # 推断意图
        intent = _infer_intent_from_tool(tool_name)

        # 分类处理工具调用
        # 1. LangChain 工具（已封装的内置工具）
        if tool_name in ["add_todo", "query_todo", "generate_commit", "auto_commit",
                         "git_pull", "git_push", "code_review", "start_project", "build_project", 
                         "diagnose_project", "stop_project", "generate_daily_report"]:
            result_text = _call_langchain_tool(tool_name, tool_args)
            return {
                "intent": intent,
                "response": result_text
            }

        # 2. 需要延迟处理的工具（由后续节点处理）
        elif tool_name in ["full_git_workflow", "data_conversion",
                           "environment_diagnostic", "terminal_command"]:
            response = {
                "intent": intent,
                "response": ""  # 由后续节点处理
            }

            # 传递额外参数（如果需要）
            if tool_name == "data_conversion":
                response.update({
                    "data_conversion_type": tool_args.get("operation", "convert"),
                    "source_format": tool_args.get("source_format", "auto"),
                    "target_format": tool_args.get("target_format", "json"),
                })

            return response

        # 3. MCP 工具（统一调用接口）- 零分支！
        else:
            # 直接调用 MCPManager，自动分发
            mcp_result = mcp_manager.call_tool(tool_name, **tool_args)

            # 检查结果是否成功（内置工具直接返回结果，MCP工具返回包装结果）
            if isinstance(mcp_result, dict) and mcp_result.get("success", True):
                # 直接格式化结果，避免工作流路由问题
                formatted_response = _format_mcp_tool_result(tool_name, mcp_result)
                return {
                    "intent": "mcp_tool_call",
                    "mcp_tool": tool_name,
                    "response": formatted_response
                }
            else:
                error_msg = mcp_result.get('error', '未知错误') if isinstance(mcp_result, dict) else str(mcp_result)
                return {
                    "intent": "error",
                    "response": f"❌ 工具调用失败: {error_msg}"
                }

    except Exception as e:
        print(f"[工具选择] ❌ 错误: {str(e)}")
        return {
            "intent": "error",
            "response": f"❌ 处理时发生错误: {str(e)}",
            "error": str(e)
        }
