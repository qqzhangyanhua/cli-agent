"""
工作流节点模块
包含所有LangGraph节点函数
"""

import json
import re
from datetime import datetime, timedelta
from langchain_core.messages import HumanMessage
from agent_config import AgentState, LLM_CONFIG, LLM_CONFIG2
from agent_memory import memory
from agent_utils import execute_terminal_command
from agent_llm import llm, llm_code
from mcp_manager import mcp_manager
from git_tools import git_tools
from file_reference_parser import parse_file_references, file_parser
from todo_manager import todo_manager
from data_converter_tools import data_converter_tools
from env_diagnostic_tools import env_diagnostic_tools
from auto_commit_tools import git_add_all, git_commit_with_message


# ============================================
# 文件引用预处理节点
# ============================================


def file_reference_processor(state: AgentState) -> dict:
    """处理文件引用，解析 @ 语法并读取文件内容"""
    user_input = state["user_input"]


    # 解析文件引用
    processed_input, file_references = parse_file_references(user_input)

    file_contents = {}
    referenced_files = []

    if file_references:
        print(f"[文件引用] 发现 {len(file_references)} 个文件引用")

        # 显示引用摘要
        summary = file_parser.format_reference_summary(file_references)
        print(summary)

        # 读取文件内容
        for ref in file_references:
            if ref.exists and not ref.is_directory:
                try:
                    # 使用 MCP 文件系统工具读取文件
                    result = mcp_manager.call_tool(
                        "filesystem", "read_file", {"path": ref.file_path}
                    )

                    if result.get("success"):
                        content = result.get("content", "")
                        file_contents[ref.file_path] = content
                        referenced_files.append(
                            {
                                "path": ref.file_path,
                                "original_ref": ref.original_text,
                                "confidence": ref.match_confidence,
                                "size": len(content),
                            }
                        )
                        print(
                            f"[文件引用] ✅ 已读取: {ref.file_path} ({len(content)} 字符)"
                        )
                    else:
                        print(f"[文件引用] ❌ 读取失败: {ref.file_path}")

                except Exception as e:
                    print(f"[文件引用] ❌ 读取错误 {ref.file_path}: {str(e)}")

            elif ref.exists and ref.is_directory:
                # 处理目录引用
                try:
                    result = mcp_manager.call_tool(
                        "filesystem", "list_directory", {"path": ref.file_path}
                    )

                    if result.get("success"):
                        dir_content = result.get("entries", [])
                        file_contents[ref.file_path] = (
                            f"目录内容: {', '.join(dir_content)}"
                        )
                        referenced_files.append(
                            {
                                "path": ref.file_path,
                                "original_ref": ref.original_text,
                                "confidence": ref.match_confidence,
                                "type": "directory",
                                "entries": len(dir_content),
                            }
                        )
                        print(
                            f"[文件引用] 📁 目录: {ref.file_path} ({len(dir_content)} 项)"
                        )

                except Exception as e:
                    print(f"[文件引用] ❌ 目录读取错误 {ref.file_path}: {str(e)}")

            else:
                print(f"[文件引用] ⚠️  文件不存在: {ref.file_path}")
                # 提供建议
                suggestions = file_parser.get_file_suggestions(
                    ref.file_path.split("/")[-1]
                )
                if suggestions:
                    print(f"[文件引用] 💡 建议的文件: {', '.join(suggestions[:3])}")

    # 更新状态
    return {
        **state,
        "original_input": user_input,
        "user_input": processed_input,
        "referenced_files": referenced_files,
        "file_contents": file_contents,
    }


# ============================================
# 意图分析和规划节点
# ============================================


def intent_analyzer(state: AgentState) -> dict:
    """分析用户意图（带上下文和文件引用）"""
    user_input = state["user_input"]
    context = memory.get_context_string()

    # 先进行基于规则的快速判断（提高准确率）
    user_input_lower = user_input.lower()

    # 查询待办的关键词
    query_keywords = [
        "有什么",
        "要做什么",
        "做什么",
        "待办",
        "任务",
        "安排",
        "查看",
        "看看",
        "有哪些",
        "什么事",
        "日程",
    ]

    # 时间相关词汇（用于判断是否涉及时间）
    time_keywords = [
        "今天",
        "明天",
        "后天",
        "周一",
        "周二",
        "周三",
        "周四",
        "周五",
        "周六",
        "周日",
        "下周",
        "点",
        "时",
        "上午",
        "下午",
        "早上",
        "晚上",
        "中午",
    ]

    # 规则1: 如果包含查询关键词 + 时间词，很可能是查询待办
    has_query_keyword = any(kw in user_input_lower for kw in query_keywords)
    has_time_word = any(kw in user_input_lower for kw in time_keywords)

    if has_query_keyword and has_time_word:
        print(f"\n[意图分析] {user_input[:50]}...")
        print(f"           规则匹配: query_todo")
        print(f"           意图: query_todo")
        return {"intent": "query_todo"}

    # 规则2: 如果包含时间词但没有疑问词，且不是疑问句，很可能是添加待办
    # 例如："明天开会"、"今天18点给陈龙打电话"
    if has_time_word and not has_query_keyword:
        # 排除疑问句（以问号结尾）
        if not user_input.strip().endswith("？") and not user_input.strip().endswith(
            "?"
        ):
            print(f"\n[意图分析] {user_input[:50]}...")
            print(f"           规则匹配: add_todo")
            print(f"           意图: add_todo")
            return {"intent": "add_todo"}

    # 如果规则没有匹配，使用 LLM 分析
    # 构建文件引用上下文
    file_context = ""
    if state.get("referenced_files"):
        file_context = "\n\n📁 用户引用的文件:\n"
        for ref in state["referenced_files"]:
            file_context += f"- {ref['path']} (来自 {ref['original_ref']})\n"

        # 添加文件内容摘要
        if state.get("file_contents"):
            file_context += "\n📄 文件内容已加载，可以直接分析和操作这些文件。\n"

    prompt = f"""你是一个智能终端助手。根据用户输入和对话历史，分析用户意图。

{context}{file_context}

当前用户输入: {user_input}

判断规则（按优先级排序，从上到下匹配）:

1. 添加待办事项 (add_todo) - 用户想记录、添加、设置一个待办或提醒
   关键特征：包含时间点 + 要做的事情
   示例：
   - "今天18点给陈龙打电话"
   - "明天上午10点开会" 
   - "周五下午3点交报告"
   - "提醒我明天买菜"
   - "记录：后天见客户"
   
2. 查询待办事项 (query_todo) - 用户想查看、询问待办事项
   关键特征：询问"有什么"、"要做什么"、"待办"、"任务"、"安排"
   示例：
   - "今天有什么要做的"
   - "明天的待办"
   - "这周有什么任务"
   - "我今天要做什么"
   - "查看我的待办"

3. Git commit (git_commit) - 生成Git commit消息

4. MCP工具 (mcp_tool_call) - 文件操作、截图、剪贴板等

5. 终端命令 (terminal_command) - 执行系统命令

6. 多步骤命令 (multi_step_command) - 需要多步骤的任务

7. 问题 (question) - 其他问答、解释、建议等

**重要**：
- 如果输入包含"今天/明天/周X + 时间 + 动作"的模式，优先判断为 add_todo
- 如果输入询问"有什么要做/待办/任务/安排"，优先判断为 query_todo
- 只有在明确不属于待办相关时，才判断为 question

只返回一个词: 'add_todo', 'query_todo', 'git_commit', 'mcp_tool_call', 'terminal_command', 'multi_step_command' 或 'question'

意图:"""

    result = llm.invoke([HumanMessage(content=prompt)])
    intent = result.content.strip().lower()

    if intent not in [
        "add_todo",
        "query_todo",
        "git_commit",
        "mcp_tool_call",
        "terminal_command",
        "multi_step_command",
        "question",
    ]:
        intent = "question"

    print(f"\n[意图分析] {user_input[:50]}...")
    print(f"           使用模型: {LLM_CONFIG['model']}")
    print(f"           意图: {intent}")

    return {"intent": intent}


def command_generator(state: AgentState) -> dict:
    """生成终端命令"""
    import platform
    
    user_input = state["user_input"]
    recent_commands = memory.get_recent_commands()
    
    # 检测操作系统
    os_type = platform.system()
    
    # 根据操作系统设置示例
    if os_type == "Windows":
        examples = """示例（Windows）:
- "列出当前目录的所有文件" -> dir 或 Get-ChildItem
- "查看Python版本" -> python --version
- "显示当前路径" -> cd
- "查看文件内容" -> type filename.txt 或 Get-Content filename.txt
- "创建目录" -> mkdir dirname
- "删除文件" -> del filename
- "复制文件" -> copy source dest
- "移动文件" -> move source dest"""
    else:
        examples = """示例（Unix/Linux/macOS）:
- "列出当前目录的所有文件" -> ls -la
- "查看Python版本" -> python3 --version
- "显示当前路径" -> pwd
- "查看文件内容" -> cat filename.txt
- "创建目录" -> mkdir dirname
- "删除文件" -> rm filename
- "复制文件" -> cp source dest
- "移动文件" -> mv source dest"""

    prompt = f"""将用户的自然语言请求转换为终端命令。

操作系统: {os_type}
{recent_commands}

当前请求: {user_input}

{examples}

**重要**: 
- 必须生成适合 {os_type} 系统的命令
- 只返回命令本身，不要解释
- 不要添加注释或说明

命令:"""

    result = llm_code.invoke([HumanMessage(content=prompt)])
    command = result.content.strip()

    print(f"[命令生成] {command}")
    print(f"           使用模型: {LLM_CONFIG2['model']}")
    print(f"           操作系统: {os_type}")

    return {"command": command}


def multi_step_planner(state: AgentState) -> dict:
    """多步骤规划"""
    import platform
    
    user_input = state["user_input"]
    recent_commands = memory.get_recent_commands()
    
    # 检测操作系统
    os_type = platform.system()

    prompt = f"""分析用户请求，返回JSON格式的执行计划。

操作系统: {os_type}
{recent_commands}

用户请求: {user_input}

返回JSON对象:
{{
  "needs_file_creation": true/false,
  "file_path": "文件路径",
  "file_content": "文件内容",
  "commands": ["命令1", "命令2"]
}}

**重要**: 生成的命令必须适合 {os_type} 系统

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
        print(f"            操作系统: {os_type}")
        print(f"            需要创建文件: {plan.get('needs_file_creation', False)}")
        print(f"            命令数量: {len(plan.get('commands', []))}")

        return {
            "needs_file_creation": plan.get("needs_file_creation", False),
            "file_path": plan.get("file_path", ""),
            "file_content": plan.get("file_content", ""),
            "commands": plan.get("commands", []),
        }
    except json.JSONDecodeError:
        print(f"[多步骤规划] JSON解析失败")
        return {
            "needs_file_creation": False,
            "file_path": "",
            "file_content": "",
            "commands": [],
            "error": "无法解析执行计划",
        }


def mcp_tool_planner(state: AgentState) -> dict:
    """规划MCP工具调用"""
    user_input = state["user_input"]

    available_tools = mcp_manager.list_available_tools()
    tools_desc = "\n".join(
        [
            f"- {t['name']}: {t['description']} (参数: {', '.join(t['params'])})"
            for t in available_tools
        ]
    )

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

        return {"mcp_tool": plan.get("tool", ""), "mcp_params": plan.get("params", {})}
    except json.JSONDecodeError as e:
        print(f"[MCP工具规划] JSON解析失败: {e}")
        return {"mcp_tool": "", "mcp_params": {}, "error": "无法解析MCP工具规划"}


def question_answerer(state: AgentState) -> dict:
    """回答用户问题（打字机效果流式输出）"""
    import time
    import sys
    import threading
    from queue import Queue
    
    user_input = state["user_input"]
    context = memory.get_context_string()
    recent_commands = memory.get_recent_commands()

    prompt = f"""你是一个友好的AI终端助手。回答用户问题，并利用对话历史提供更好的帮助。

{context}

{recent_commands}

当前问题: {user_input}

请简洁但全面地回答用户的问题。如果用户提到"刚才"、"之前"等词，请参考对话历史。

回答:"""

    print(f"[问题回答] 生成回答")
    print(f"           使用模型: {LLM_CONFIG['model']}")
    print()  # 空行
    print("─" * 80)
    print("🤖 助手: ", end="", flush=True)

    # 打字机效果流式输出
    try:
        response = ""
        char_queue = Queue()
        output_finished = threading.Event()
        
        def typewriter_output():
            """打字机输出线程"""
            while not output_finished.is_set() or not char_queue.empty():
                try:
                    # 从队列获取字符，超时避免死锁
                    char = char_queue.get(timeout=0.1)
                    print(char, end="", flush=True)
                    
                    # 智能打字机延迟
                    if char in '，。！？；：':  # 标点符号稍微停顿
                        time.sleep(0.06)
                    elif char == ' ':  # 空格快速跳过
                        time.sleep(0.01)
                    else:  # 普通字符
                        time.sleep(0.03)
                    
                except:
                    continue
        
        # 启动打字机输出线程
        output_thread = threading.Thread(target=typewriter_output, daemon=True)
        output_thread.start()
        
        # 收集LLM输出并逐字符放入队列
        for chunk in llm.stream([HumanMessage(content=prompt)]):
            if hasattr(chunk, "content") and chunk.content:
                content = chunk.content
                response += content
                
                # 逐字符放入队列
                for char in content:
                    char_queue.put(char)
        
        # 标记输出完成
        output_finished.set()
        
        # 等待输出线程完成
        output_thread.join(timeout=5.0)  # 最多等待5秒
        
        # 确保所有字符都输出完毕
        while not char_queue.empty():
            try:
                char = char_queue.get_nowait()
                print(char, end="", flush=True)
            except:
                break

        print()  # 换行
        print("─" * 80)

        return {"response": response}

    except Exception as e:
        error_msg = f"❌ 生成回答失败: {str(e)}"
        print(error_msg)
        print("─" * 80)
        return {"response": error_msg, "error": str(e)}


# ============================================
# 执行节点
# ============================================


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


# ============================================
# 响应格式化节点
# ============================================


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


# ============================================
# Git相关节点
# ============================================


def git_commit_generator(state: AgentState) -> dict:
    """
    生成Git commit消息
    调用 git_commit_tools 中的实现，避免代码重复
    """
    from git_commit_tools import generate_commit_message_tool_func
    
    print(f"[Git Commit] 调用Git commit工具...")
    
    try:
        # 调用 git_commit_tools 中更完善的实现
        response = generate_commit_message_tool_func()
        
        print(f"[Git Commit] ✅ 生成完成")
        return {"response": response}
        
    except Exception as e:
        error_msg = f"❌ Git commit消息生成失败: {str(e)}"
        print(f"[Git Commit] {error_msg}")
        return {"response": error_msg, "error": str(e)}


# ============================================
# 待办事项处理节点
# ============================================


def todo_processor(state: AgentState) -> dict:
    """处理待办事项的添加和查询"""
    user_input = state["user_input"]
    intent = state["intent"]

    print(f"\n[待办处理] 处理待办事项...")
    print(f"           意图: {intent}")

    if intent == "add_todo":
        # 使用LLM解析待办信息
        prompt = f"""从用户输入中提取待办事项信息，返回JSON格式。

用户输入: {user_input}

需要提取:
1. date: 日期（格式：YYYY-MM-DD）。如果用户说"今天"，使用今天日期；"明天"使用明天日期；具体日期按实际解析
2. time: 时间（格式：HH:MM），如果没有明确时间，返回空字符串
3. content: 待办内容（简洁描述，去掉日期时间信息）

今天是: {datetime.now().strftime("%Y-%m-%d")}

示例:
输入: "今天18点我要给陈龙打电话"
输出: {{"date": "2024-01-22", "time": "18:00", "content": "给陈龙打电话"}}

输入: "明天上午10点开会"
输出: {{"date": "2024-01-23", "time": "10:00", "content": "开会"}}

输入: "提醒我周五下午3点半交报告"
输出: {{"date": "2024-01-26", "time": "15:30", "content": "交报告"}}

只返回JSON，不要其他内容:"""

        result = llm.invoke([HumanMessage(content=prompt)])
        response_text = result.content.strip()

        # 提取JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        try:
            parsed = json.loads(response_text)
            date = parsed.get("date", "")
            time = parsed.get("time", "")
            content = parsed.get("content", "")

            print(f"[待办处理] 解析结果 - 日期:{date} 时间:{time} 内容:{content}")

            # 验证日期格式
            if date:
                try:
                    datetime.strptime(date, "%Y-%m-%d")
                except ValueError:
                    print(f"[待办处理] ❌ 日期格式无效: {date}")
                    return {
                        "response": f"❌ 日期格式无效: {date}\n\n请使用正确的日期格式，例如：「今天18点给陈龙打电话」",
                        "error": "Invalid date format",
                    }

            # 验证时间格式（如果提供了时间）
            if time:
                try:
                    datetime.strptime(time, "%H:%M")
                except ValueError:
                    print(f"[待办处理] ⚠️  时间格式异常: {time}，将忽略时间")
                    time = ""

            if date and content:
                # 添加待办
                todo_item = todo_manager.add_todo(date, time, content)

                if todo_item:
                    response = f"✅ 待办已添加！\n\n"
                    response += f"📅 日期: {date}\n"
                    if time:
                        response += f"⏰ 时间: {time}\n"
                    response += f"📝 内容: {content}\n"
                    response += f"\n💡 你可以随时问我「今天有什么要做的？」或「{date}有什么待办？」来查看待办事项。"
                else:
                    response = "❌ 添加待办失败，请重试。"
            else:
                response = "❌ 无法解析待办信息，请提供更明确的日期和内容。\n\n示例：「今天18点给陈龙打电话」"

            return {
                "response": response,
                "todo_action": "add",
                "todo_date": date,
                "todo_time": time,
                "todo_content": content,
            }

        except json.JSONDecodeError as e:
            print(f"[待办处理] JSON解析失败: {e}")
            return {
                "response": "❌ 解析待办信息失败，请重试。\n\n示例：「今天18点给陈龙打电话」",
                "error": str(e),
            }

    elif intent == "query_todo":
        # 使用LLM解析查询意图
        prompt = f"""从用户输入中提取查询信息，返回JSON格式。

用户输入: {user_input}

需要提取:
1. query_type: 查询类型
   - "today": 查询今天
   - "date": 查询特定日期
   - "range": 查询日期范围
   - "upcoming": 查询未来几天
   - "search": 搜索关键词
2. date: 日期（YYYY-MM-DD），适用于 date 类型
3. start_date: 开始日期，适用于 range 类型
4. end_date: 结束日期，适用于 range 类型
5. days: 天数，适用于 upcoming 类型
6. keyword: 搜索关键词，适用于 search 类型

今天是: {datetime.now().strftime("%Y-%m-%d")}

示例:
"今天有什么要做的？" -> {{"query_type": "today"}}
"明天有什么待办？" -> {{"query_type": "date", "date": "2024-01-23"}}
"这周有什么任务？" -> {{"query_type": "range", "start_date": "2024-01-22", "end_date": "2024-01-28"}}
"未来3天的待办" -> {{"query_type": "upcoming", "days": 3}}
"陈龙相关的待办" -> {{"query_type": "search", "keyword": "陈龙"}}

只返回JSON:"""

        result = llm.invoke([HumanMessage(content=prompt)])
        response_text = result.content.strip()

        # 提取JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        try:
            parsed = json.loads(response_text)
            query_type = parsed.get("query_type", "today")

            print(f"[待办处理] 查询类型: {query_type}")

            response = ""

            if query_type == "today":
                todos = todo_manager.get_today_todos()
                date = datetime.now().strftime("%Y-%m-%d")
                response = f"📅 今天（{date}）的待办:\n\n"
                if todos:
                    response += todo_manager.format_todos_display(todos)
                else:
                    response += "📭 今天没有待办事项"

            elif query_type == "date":
                date = parsed.get("date", "")
                if date:
                    todos = todo_manager.get_todos(date)
                    response = f"📅 {date} 的待办:\n\n"
                    if todos:
                        response += todo_manager.format_todos_display(todos)
                    else:
                        response += "📭 这天没有待办事项"
                else:
                    response = "❌ 无法解析日期"

            elif query_type == "range":
                start_date = parsed.get("start_date", "")
                end_date = parsed.get("end_date", "")
                if start_date and end_date:
                    todos_by_date = todo_manager.get_todos_by_range(
                        start_date, end_date
                    )
                    response = f"📅 {start_date} 到 {end_date} 的待办:\n\n"
                    if todos_by_date:
                        for date, todos in sorted(todos_by_date.items()):
                            response += f"\n📆 {date}\n"
                            response += todo_manager.format_todos_display(todos) + "\n"
                    else:
                        response += "📭 这个时间段没有待办事项"
                else:
                    response = "❌ 无法解析日期范围"

            elif query_type == "upcoming":
                days = parsed.get("days", 7)
                todos_by_date = todo_manager.get_upcoming_todos(days)
                response = f"📅 未来 {days} 天的待办:\n\n"
                if todos_by_date:
                    for date, todos in sorted(todos_by_date.items()):
                        response += f"\n📆 {date}\n"
                        response += todo_manager.format_todos_display(todos) + "\n"
                else:
                    response += "📭 未来几天没有待办事项"

            elif query_type == "search":
                keyword = parsed.get("keyword", "")
                if keyword:
                    results = todo_manager.search_todos(keyword)
                    response = f"🔍 搜索「{keyword}」的结果:\n\n"
                    if results:
                        for date, todos in sorted(results.items()):
                            response += f"\n📆 {date}\n"
                            response += todo_manager.format_todos_display(todos) + "\n"
                    else:
                        response += f"📭 没有找到包含「{keyword}」的待办事项"
                else:
                    response = "❌ 请提供搜索关键词"

            return {
                "response": response,
                "todo_action": "query",
                "todo_result": response,
            }

        except json.JSONDecodeError as e:
            print(f"[待办处理] JSON解析失败: {e}")
            return {
                "response": "❌ 解析查询失败，请重试。\n\n示例：「今天有什么要做的？」",
                "error": str(e),
            }

    else:
        return {"response": "❌ 未知的待办操作", "error": "Unknown todo intent"}


# ============================================
# 数据转换节点
# ============================================


def data_conversion_processor(state: AgentState) -> dict:
    """
    数据转换处理节点
    支持 JSON/CSV/YAML 等格式之间的转换、验证和美化
    """
    user_input = state["user_input"]
    file_contents = state.get("file_contents", {})
    
    print(f"\n[数据转换] 处理请求...")
    
    # 使用 LLM 分析用户意图
    file_info = ""
    if file_contents:
        file_paths = list(file_contents.keys())
        file_info = f"\n\n📁 用户引用的文件:\n{chr(10).join(['- ' + p for p in file_paths])}"
    
    prompt = f"""分析用户的数据转换请求，返回JSON格式。

用户请求: {user_input}{file_info}

支持的操作类型:
1. convert: 格式转换 (json↔csv, json↔yaml, yaml↔json, xml→json)
2. validate: 格式验证
3. beautify: 格式美化

支持的格式: json, yaml, csv, xml

返回JSON:
{{
  "operation": "convert/validate/beautify",
  "source_format": "源格式或auto",
  "target_format": "目标格式(仅convert需要)",
  "file_path": "要处理的文件路径(如果用户引用了文件)"
}}

示例:
"转换为CSV" -> {{"operation": "convert", "source_format": "auto", "target_format": "csv"}}
"验证JSON" -> {{"operation": "validate", "source_format": "json"}}
"美化JSON" -> {{"operation": "beautify", "source_format": "json"}}

只返回JSON:"""
    
    result = llm.invoke([HumanMessage(content=prompt)])
    response_text = result.content.strip()
    
    # 提取JSON
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()
    
    try:
        parsed = json.loads(response_text)
        operation = parsed.get("operation", "convert")
        source_format = parsed.get("source_format", "auto")
        target_format = parsed.get("target_format", "json")
        file_path = parsed.get("file_path", "")
        
        print(f"[数据转换] 操作:{operation} 源格式:{source_format} 目标格式:{target_format}")
        
        # 获取文件内容
        content = ""
        if file_path and file_path in file_contents:
            content = file_contents[file_path]
        elif file_contents:
            # 使用第一个文件
            content = list(file_contents.values())[0]
            file_path = list(file_contents.keys())[0]
        else:
            return {
                "response": "❌ 数据转换失败：未找到要处理的文件\n\n请使用 @ 引用要转换的文件，例如: @data.json 转换为CSV",
                "error": "No file content"
            }
        
        # 执行操作
        response = ""
        
        if operation == "convert":
            # 格式转换
            result = data_converter_tools.convert(
                content=content,
                source_format=source_format,
                target_format=target_format,
                file_path=file_path
            )
            
            if result["success"]:
                converted_content = result["result"]
                detected_format = result.get("source_format", source_format)
                
                response = f"✅ 数据转换成功\n\n"
                response += f"📄 源文件: {file_path}\n"
                response += f"📊 格式: {detected_format} → {target_format}\n"
                response += f"📏 大小: {len(content)} → {result['size']} 字符\n\n"
                response += f"转换结果:\n"
                response += "─" * 80 + "\n"
                
                # 限制输出长度
                if len(converted_content) > 2000:
                    response += converted_content[:2000] + "\n\n... (结果太长，已截断)\n"
                else:
                    response += converted_content + "\n"
                
                response += "─" * 80 + "\n\n"
                response += f"💡 提示: 可以将结果保存到文件"
                
                return {
                    "response": response,
                    "conversion_result": converted_content,
                    "source_format": detected_format,
                    "target_format": target_format
                }
            else:
                return {
                    "response": f"❌ 数据转换失败\n\n错误: {result['error']}",
                    "error": result["error"]
                }
        
        elif operation == "validate":
            # 格式验证
            result = data_converter_tools.validate(content, source_format)
            
            if result["success"]:
                response = f"🔍 数据验证结果\n\n"
                response += f"📄 文件: {file_path}\n"
                response += f"📊 格式: {source_format}\n"
                response += f"🎯 结果: {result['message']}\n"
                
                if not result["valid"]:
                    response += f"\n💡 提示: 请检查文件格式是否正确"
                
                return {"response": response}
            else:
                return {
                    "response": f"❌ 验证失败\n\n错误: {result['message']}",
                    "error": result["message"]
                }
        
        elif operation == "beautify":
            # 格式美化
            result = data_converter_tools.beautify(content, source_format)
            
            if result["success"]:
                beautified_content = result["result"]
                
                response = f"✨ 格式美化完成\n\n"
                response += f"📄 文件: {file_path}\n"
                response += f"📊 格式: {source_format}\n"
                response += f"📏 大小: {result['original_size']} → {result['formatted_size']} 字符\n\n"
                response += f"美化结果:\n"
                response += "─" * 80 + "\n"
                
                if len(beautified_content) > 2000:
                    response += beautified_content[:2000] + "\n\n... (结果太长，已截断)\n"
                else:
                    response += beautified_content + "\n"
                
                response += "─" * 80
                
                return {
                    "response": response,
                    "conversion_result": beautified_content
                }
            else:
                return {
                    "response": f"❌ 美化失败\n\n错误: {result['error']}",
                    "error": result["error"]
                }
    
    except json.JSONDecodeError as e:
        print(f"[数据转换] JSON解析失败: {e}")
        return {
            "response": "❌ 解析转换请求失败，请重试。\n\n示例：@data.json 转换为CSV",
            "error": str(e)
        }
    except Exception as e:
        print(f"[数据转换] 错误: {e}")
        return {
            "response": f"❌ 数据转换出错: {str(e)}",
            "error": str(e)
        }


# ============================================
# 环境诊断节点
# ============================================


def environment_diagnostic_processor(state: AgentState) -> dict:
    """
    环境诊断处理节点
    检测和诊断开发环境配置
    """
    print(f"\n[环境诊断] 开始诊断...")
    
    try:
        # 执行完整诊断
        result = env_diagnostic_tools.full_diagnostic()
        
        if result["success"]:
            report = result["report"]
            
            # 格式化报告
            formatted_report = env_diagnostic_tools.format_report(report)
            
            print(f"[环境诊断] ✅ 诊断完成")
            
            return {
                "response": formatted_report,
                "diagnostic_result": json.dumps(report, ensure_ascii=False)
            }
        else:
            error_msg = result.get("error", "未知错误")
            print(f"[环境诊断] ❌ 诊断失败: {error_msg}")
            return {
                "response": f"❌ 环境诊断失败\n\n错误: {error_msg}",
                "error": error_msg
            }
    
    except Exception as e:
        print(f"[环境诊断] ❌ 异常: {e}")
        return {
            "response": f"❌ 环境诊断出错: {str(e)}",
            "error": str(e)
        }


# ============================================
# Git 自动提交工作流节点
# ============================================

def git_add_node(state: AgentState) -> dict:
    """
    Git 工作流节点 1: 执行 git add .
    暂存所有变更
    """
    print(f"\n📦 [Git 工作流 1/3] 暂存变更...")
    
    try:
        result = git_add_all()
        
        if result["success"]:
            files_count = result.get("files_count", 0)
            print(f"[Git Add] ✅ {result['message']}")
            
            return {
                "git_add_success": True,
                "git_files_count": files_count,
                "response": result["message"]
            }
        else:
            error_msg = result.get("error", "git add 失败")
            print(f"[Git Add] ❌ {error_msg}")
            return {
                "git_add_success": False,
                "response": f"❌ Git 提交流程终止\n\n{error_msg}",
                "error": error_msg
            }
    
    except Exception as e:
        print(f"[Git Add] ❌ 异常: {e}")
        return {
            "git_add_success": False,
            "response": f"❌ Git add 执行失败: {str(e)}",
            "error": str(e)
        }


def git_commit_message_generator_node(state: AgentState) -> dict:
    """
    Git 工作流节点 2: 生成 commit 消息
    基于 git diff 分析代码变更并生成符合规范的 commit 消息
    """
    print(f"\n💡 [Git 工作流 2/3] 生成 commit 消息...")
    
    try:
        # 分析变更
        analysis = git_tools.analyze_changes()
        
        if not analysis["success"]:
            error_msg = analysis.get("error", "分析变更失败")
            print(f"[Commit 生成] ❌ {error_msg}")
            return {
                "git_commit_message_generated": False,
                "response": f"❌ Git 提交流程终止\n\n步骤 1: ✅ 已暂存变更\n步骤 2: ❌ {error_msg}",
                "error": error_msg
            }
        
        # 准备 diff 内容
        if analysis['has_staged']:
            diff_content = analysis['staged_diff']
        else:
            error_msg = "没有已暂存的变更"
            return {
                "git_commit_message_generated": False,
                "response": f"❌ Git 提交流程终止\n\n步骤 1: ✅ 已暂存变更\n步骤 2: ❌ {error_msg}",
                "error": error_msg
            }
        
        # 获取文件状态
        status_lines = analysis['status'].split('\n')
        
        # 分类统计文件变更
        deleted_files = []
        modified_files = []
        added_files = []
        
        for line in status_lines:
            if not line.strip():
                continue
            if line.startswith(' D') or line.startswith('D '):
                deleted_files.append(line[3:])
            elif line.startswith(' M') or line.startswith('M '):
                modified_files.append(line[3:])
            elif line.startswith('??') or line.startswith('A '):
                added_files.append(line[3:])
        
        file_stats = []
        if deleted_files:
            file_stats.append(f"删除 {len(deleted_files)} 个")
        if modified_files:
            file_stats.append(f"修改 {len(modified_files)} 个")
        if added_files:
            file_stats.append(f"新增 {len(added_files)} 个")
        
        file_stats_str = "、".join(file_stats) if file_stats else "未知变更"
        
        # 限制 diff 长度
        max_diff_length = 8000
        if len(diff_content) > max_diff_length:
            diff_content = diff_content[:max_diff_length] + "\n\n... (diff太长，已截断)"
        
        # 获取最近的 commits 作为参考
        recent_commits_str = "\n".join(analysis.get('recent_commits', [])[:5])
        
        # 生成 commit 消息
        prompt = f"""你是一个专业的Git commit消息生成器。基于下面的代码变更，生成简洁、精确的commit消息。

📊 变更统计:
- 总计: {len(analysis['files_changed'])} 个文件 ({file_stats_str})

📄 代码变更内容:
```diff
{diff_content}
```

📜 最近的commit记录(参考风格):
{recent_commits_str if recent_commits_str else '(暂无历史commit)'}

🎯 要求:
1. 遵循 Conventional Commits 规范
2. 使用中文描述
3. 格式: <type>: <subject>
4. type选择: feat/fix/refactor/docs/perf/test/chore
5. subject要具体描述变更内容

只返回一行commit消息，不要其他内容。"""
        
        result = llm_code.invoke([HumanMessage(content=prompt)])
        commit_message = result.content.strip()
        
        # 清理可能的 markdown 格式
        if commit_message.startswith("```"):
            lines = commit_message.split('\n')
            commit_message = '\n'.join(lines[1:-1]) if len(lines) > 2 else commit_message
        
        # 转义双引号
        commit_message = commit_message.replace('"', "'")
        
        print(f"[Commit 生成] ✅ 生成完成")
        print(f"[Commit 生成] 消息: {commit_message}")
        
        return {
            "git_commit_message_generated": True,
            "git_commit_message": commit_message,
            "git_file_stats": file_stats_str,
            "response": f"✅ 已生成 commit 消息:\n  {commit_message}"
        }
    
    except Exception as e:
        print(f"[Commit 生成] ❌ 异常: {e}")
        return {
            "git_commit_message_generated": False,
            "response": f"❌ Git 提交流程终止\n\n步骤 1: ✅ 已暂存变更\n步骤 2: ❌ 生成 commit 消息失败: {str(e)}",
            "error": str(e)
        }


def git_commit_executor_node(state: AgentState) -> dict:
    """
    Git 工作流节点 3: 执行 git commit
    使用生成的 commit 消息提交代码
    """
    print(f"\n✍️  [Git 工作流 3/3] 提交代码...")
    
    commit_message = state.get("git_commit_message", "")
    files_count = state.get("git_files_count", 0)
    file_stats = state.get("git_file_stats", "")
    
    if not commit_message:
        error_msg = "缺少 commit 消息"
        return {
            "response": f"❌ Git 提交流程终止\n\n步骤 1: ✅ 已暂存变更\n步骤 2: ✅ 已生成消息\n步骤 3: ❌ {error_msg}",
            "error": error_msg
        }
    
    try:
        result = git_commit_with_message(commit_message)
        
        if result["success"]:
            commit_hash = result.get("commit_hash", "")
            print(f"[Git Commit] ✅ {result['message']}")
            
            # 生成最终响应
            response = f"""
🎉 Git 自动提交流程完成！

{'─'*60}
📦 步骤 1: ✅ 已暂存 {files_count} 个文件 ({file_stats})

💡 步骤 2: ✅ 生成 commit 消息
  {commit_message}

✍️  步骤 3: ✅ 代码已提交 {f'(commit: {commit_hash[:7]})' if commit_hash else ''}
{'─'*60}

💡 提示: 使用 'git log' 查看提交历史
"""
            
            return {
                "response": response,
                "git_commit_success": True,
                "git_commit_hash": commit_hash
            }
        else:
            error_msg = result.get("error", "git commit 失败")
            print(f"[Git Commit] ❌ {error_msg}")
            
            response = f"""❌ Git 提交流程失败

步骤 1: ✅ 已暂存 {files_count} 个文件
步骤 2: ✅ 已生成 commit 消息
步骤 3: ❌ {error_msg}

你可以手动执行:
  git commit -m "{commit_message}"
"""
            
            return {
                "response": response,
                "git_commit_success": False,
                "error": error_msg
            }
    
    except Exception as e:
        print(f"[Git Commit] ❌ 异常: {e}")
        
        response = f"""❌ Git 提交流程失败

步骤 1: ✅ 已暂存 {files_count} 个文件
步骤 2: ✅ 已生成 commit 消息
步骤 3: ❌ 执行失败: {str(e)}

你可以手动执行:
  git commit -m "{commit_message}"
"""
        
        return {
            "response": response,
            "git_commit_success": False,
            "error": str(e)
        }
