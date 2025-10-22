"""
智能工具调用节点 - 利用 LangChain 的 Tool Calling 能力
让 LLM 自主决定调用哪个工具
"""

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.prebuilt import create_react_agent
from datetime import datetime
import json

from agent_config import AgentState
from agent_llm import llm
from todo_tools import todo_tools, add_todo_tool, query_todo_tool
from git_commit_tools import generate_commit_tool
from code_review_tools import code_review_tool


def create_tool_agent():
    """创建一个支持工具调用的 ReAct 代理"""

    system_prompt = f"""你是一个智能终端助手，可以帮助用户管理待办事项。

今天的日期是: {datetime.now().strftime("%Y-%m-%d %A")}

当用户提到相对日期时，请转换为具体日期：
- 今天 = {datetime.now().strftime("%Y-%m-%d")}
- 明天 = {(datetime.now() + __import__('datetime').timedelta(days=1)).strftime("%Y-%m-%d")}
- 后天 = {(datetime.now() + __import__('datetime').timedelta(days=2)).strftime("%Y-%m-%d")}

你有以下工具可以使用：
1. add_todo - 添加待办事项
2. query_todo - 查询待办事项

请根据用户的输入，判断用户意图并调用合适的工具。

重要规则：
- 如果用户说"今天18点给XX打电话"，这是添加待办，应该调用 add_todo
- 如果用户问"今天有什么要做的"，这是查询待办，应该调用 query_todo
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


# 简化版：如果 ReAct Agent 太复杂，可以用简单的工具选择逻辑
def simple_tool_calling_node(state: AgentState, enable_streaming: bool = True) -> dict:
    """
    简化版工具调用节点
    使用 LLM 选择工具，然后手动调用

    Args:
        state: 当前状态
        enable_streaming: 是否启用流式输出（问答时使用）
    """
    user_input = state["user_input"]

    print(f"\n[工具选择] 分析用户意图...")

    # 让 LLM 选择工具和参数
    prompt = f"""你是一个工具选择助手。根据用户输入，选择合适的工具并提取参数。

今天是: {datetime.now().strftime("%Y-%m-%d")}

可用工具:
1. add_todo - 添加待办事项
   参数: date (YYYY-MM-DD), time (HH:MM, 可选), content (字符串)

2. query_todo - 查询待办事项
   参数: type (today/date/range/search), date (可选), start_date (可选), end_date (可选), keyword (可选)

3. generate_commit - 生成Git commit消息
   参数: 无（自动分析git diff）
   适用场景: "生成commit日志"、"生成commit消息"、"帮我写commit message"

4. code_review - 代码审查
   参数: 无（自动分析git diff）
   适用场景: "代码审查"、"code review"、"检查代码"、"review代码"、"对当前代码进行code-review"

5. data_conversion - 数据格式转换
   参数: operation (convert/validate/beautify), source_format (json/yaml/csv/xml/auto), target_format (可选)
   适用场景: "@data.json 转换为CSV"、"验证JSON格式"、"美化JSON"
   注意: 需要用户使用 @ 引用文件

6. environment_diagnostic - 环境诊断
   参数: 无
   适用场景: "检查开发环境"、"诊断环境"、"环境检测"

7. get_stock_info - 获取股票实时信息
   参数: stock_code (股票代码或名称)
   适用场景: "获取XX股票价格"、"查询XX股价"、"XX股票最新价格"、"XX股票信息"

8. terminal_command - 执行终端命令
   参数: 无（自动生成命令）
   适用场景: 
   - "列出当前目录下的json文件"、"ls *.json"
   - "查看Python版本"、"python --version"
   - "显示当前路径"、"pwd"
   - "创建文件夹"、"mkdir xxx"
   - "删除文件"、"rm xxx"
   - "查看文件内容"、"cat xxx"
   - 任何可以用终端命令完成的操作

9. none - 不需要工具（普通问答）

用户输入: {user_input}

请返回 JSON 格式:
{{
    "tool": "工具名称",
    "args": {{参数字典}}
}}

只返回 JSON，不要其他内容。

注意：
- 将相对日期（今天、明天等）转换为具体日期
- 如果用户提到"commit"、"提交"、"git"相关，优先选择 generate_commit
- 如果用户提到"code review"、"代码审查"、"检查代码"、"review"，优先选择 code_review
- 如果用户使用 @ 引用了文件并要求"转换"、"验证"、"美化"，选择 data_conversion
- 如果用户要求"检查环境"、"诊断环境"、"环境检测"，选择 environment_diagnostic
- 如果用户要求查询股票信息（"获取XX价格"、"XX股价"、"XX股票"、"股票信息"），选择 get_stock_info
- 如果用户要求执行系统操作（列出文件、查看版本、创建删除文件等），选择 terminal_command
- 终端命令的关键词：列出、查看、显示、创建、删除、运行、执行、ls、cat、mkdir、rm、pwd、python、node等
- 如果无法判断，返回 {{"tool": "none", "args": {{}}}}
"""

    try:
        result = llm.invoke([HumanMessage(content=prompt)])
        response_text = result.content.strip()

        # 提取 JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        tool_choice = json.loads(response_text)
        tool_name = tool_choice.get("tool", "none")
        tool_args = tool_choice.get("args", {})

        print(f"[工具选择] 选择工具: {tool_name}")
        print(f"[工具选择] 参数: {tool_args}")

        # 调用工具
        if tool_name == "add_todo":
            result_text = add_todo_tool.func(json.dumps(tool_args, ensure_ascii=False))
            return {
                "intent": "add_todo",
                "response": result_text
            }

        elif tool_name == "query_todo":
            result_text = query_todo_tool.func(json.dumps(tool_args, ensure_ascii=False))
            return {
                "intent": "query_todo",
                "response": result_text
            }

        elif tool_name == "generate_commit":
            result_text = generate_commit_tool.func("")
            return {
                "intent": "git_commit",
                "response": result_text
            }

        elif tool_name == "code_review":
            result_text = code_review_tool.func("")
            return {
                "intent": "code_review",
                "response": result_text
            }

        elif tool_name == "data_conversion":
            # 数据转换需要传递到专门的节点处理
            return {
                "intent": "data_conversion",
                "data_conversion_type": tool_args.get("operation", "convert"),
                "source_format": tool_args.get("source_format", "auto"),
                "target_format": tool_args.get("target_format", "json"),
                "response": ""  # 由节点处理
            }

        elif tool_name == "environment_diagnostic":
            # 环境诊断需要传递到专门的节点处理
            return {
                "intent": "environment_diagnostic",
                "response": ""  # 由节点处理
            }

        elif tool_name == "get_stock_info":
            # 股票查询需要传递到MCP工具处理
            return {
                "intent": "mcp_tool_call",
                "mcp_tool": "get_stock_info",
                "mcp_params": tool_args,
                "response": ""  # 由MCP节点处理
            }

        elif tool_name == "terminal_command":
            # 终端命令需要传递到命令生成和执行节点
            return {
                "intent": "terminal_command",
                "response": ""  # 由后续节点处理
            }

        else:
            # 普通问答，需要继续处理
            return {
                "intent": "question",
                "response": ""  # 需要后续节点生成回答
            }

    except Exception as e:
        print(f"[工具选择] ❌ 错误: {str(e)}")
        return {
            "intent": "error",
            "response": f"❌ 处理时发生错误: {str(e)}",
            "error": str(e)
        }
