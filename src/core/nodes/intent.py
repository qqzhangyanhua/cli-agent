"""
意图分析和规划节点
包含意图识别、命令生成、多步骤规划、MCP工具规划
"""

import json
import platform
from datetime import datetime
from langchain_core.messages import HumanMessage

from src.core.agent_config import AgentState, LLM_CONFIG, LLM_CONFIG2
from src.core.agent_memory import memory
from src.core.agent_llm import llm, llm_code
from src.mcp.mcp_manager import mcp_manager
from src.core.json_utils import extract_json_str, safe_json_loads


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
    # 例如：\"明天开会\"、\"今天18点给陈龙打电话\"
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
   - \"今天18点给陈龙打电话\"
   - \"明天上午10点开会\"
   - \"周五下午3点交报告\"
   - \"提醒我明天买菜\"
   - \"记录：后天见客户\"

2. 查询待办事项 (query_todo) - 用户想查看、询问待办事项
   关键特征：询问\"有什么\"、\"要做什么\"、\"待办\"、\"任务\"、\"安排\"
   示例：
   - \"今天有什么要做的\"
   - \"明天的待办\"
   - \"这周有什么任务\"
   - \"我今天要做什么\"
   - \"查看我的待办\"

3. Git commit (git_commit) - 生成Git commit消息

4. MCP工具 (mcp_tool_call) - 文件操作、截图、剪贴板等

5. 终端命令 (terminal_command) - 执行系统命令
   关键特征：包含\"打开\"、\"目录\"、\"文件夹\"、\"终端\"等操作词汇
   示例：
   - \"打开当前文件所在目录\"
   - \"在新的终端打开当前目录\"
   - \"打开这个文件夹\"
   - \"用文件管理器打开\"
   - \"在Finder中打开\"
   - \"在资源管理器中打开\"

6. 多步骤命令 (multi_step_command) - 需要多步骤的任务

7. 问题 (question) - 其他问答、解释、建议等

**重要**：
- 如果输入包含\"今天/明天/周X + 时间 + 动作\"的模式，优先判断为 add_todo
- 如果输入询问\"有什么要做/待办/任务/安排\"，优先判断为 query_todo
- 如果输入包含\"打开\"+\"目录/文件夹/终端\"等词汇，优先判断为 terminal_command
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
    user_input = state["user_input"]
    recent_commands = memory.get_recent_commands()

    # 检测操作系统
    os_type = platform.system()

    # 根据操作系统设置示例
    if os_type == "Windows":
        examples = """示例(Windows):
- \"列出当前目录的所有文件\" -> dir 或 Get-ChildItem
- \"查看Python版本\" -> python --version
- \"显示当前路径\" -> cd
- \"查看文件内容\" -> type filename.txt 或 Get-Content filename.txt
- \"创建目录\" -> mkdir dirname
- \"删除文件\" -> del filename
- \"复制文件\" -> copy source dest
- \"移动文件\" -> move source dest
- \"打开当前目录\" -> explorer .
- \"打开文件夹\" -> explorer .
- \"打开当前文件所在目录\" -> explorer .
- \"打开终端\" -> start cmd /k \"cd /d %cd%\"
- \"在新的终端打开当前目录\" -> start cmd /k \"cd /d %cd%\"
- \"用文件管理器打开\" -> explorer ."""
    else:
        examples = """示例(Unix/Linux/macOS):
- \"列出当前目录的所有文件\" -> ls -la
- \"查看Python版本\" -> python3 --version
- \"显示当前路径\" -> pwd
- \"查看文件内容\" -> cat filename.txt
- \"创建目录\" -> mkdir dirname
- \"删除文件\" -> rm filename
- \"复制文件\" -> cp source dest
- \"移动文件\" -> mv source dest
- \"打开当前目录\" -> open .
- \"打开文件夹\" -> open .
- \"打开当前文件所在目录\" -> open .
- \"打开终端\" -> open -a Terminal .
- \"在新的终端打开当前目录\" -> open -a Terminal .
- \"用文件管理器打开\" -> open ."""

    prompt = f"""将用户的自然语言请求转换为终端命令.

操作系统: {os_type}
{recent_commands}

当前请求: {user_input}

{examples}

**重要语义区分**:
- \"打开当前目录\" -> 打开工作目录本身 (使用 . )
- \"打开文件夹\" -> 打开工作目录本身 (使用 . )
- \"打开当前文件所在目录\" -> 打开工作目录本身 (使用 . )
- \"打开终端\" -> 在当前工作目录打开新终端 (macOS: open -a Terminal ., Windows: start cmd /k \"cd /d %cd%\")

**重要**:
- 必须生成适合 {os_type} 系统的命令
- 只返回命令本身, 不要解释
- 不要添加注释或说明
- 注意区分打开当前目录(.)和父目录(..)的语义

命令:"""

    result = llm_code.invoke([HumanMessage(content=prompt)])
    command = result.content.strip()

    print(f"[命令生成] {command}")
    print(f"           使用模型: {LLM_CONFIG2['model']}")
    print(f"           操作系统: {os_type}")

    return {"command": command}


def multi_step_planner(state: AgentState) -> dict:
    """多步骤规划"""
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
    plan_text = extract_json_str(result.content.strip())

    obj, err = safe_json_loads(plan_text)
    if err:
        print(f"[多步骤规划] JSON解析失败: {err}")
        return {
            "needs_file_creation": False,
            "file_path": "",
            "file_content": "",
            "commands": [],
            "error": "无法解析执行计划",
        }
    try:
        plan = obj
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
输入: \"读取README.md文件\"
输出: {{
  "tool": "fs_read",
  "params": {{"file_path": "README.md"}}
}}

只返回JSON:"""

    result = llm_code.invoke([HumanMessage(content=prompt)])
    plan_text = extract_json_str(result.content.strip())
    obj, err = safe_json_loads(plan_text)
    if err:
        print(f"[MCP工具规划] JSON解析失败: {err}")
        return {"mcp_tool": "", "mcp_params": {}, "error": "无法解析MCP工具规划"}
    try:
        plan = obj
        print(f"[MCP工具规划] 使用模型: {LLM_CONFIG2['model']}")
        print(f"            工具: {plan.get('tool', 'unknown')}")
        print(f"            参数: {plan.get('params', {})}")

        return {"mcp_tool": plan.get("tool", ""), "mcp_params": plan.get("params", {})}
    except Exception as e:
        print(f"[MCP工具规划] 解析失败: {e}")
        return {"mcp_tool": "", "mcp_params": {}, "error": "无法解析MCP工具规划"}
