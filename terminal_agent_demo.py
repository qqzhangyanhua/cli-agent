"""
AI智能体终端控制工具Demo
演示AI Agent如何通过自然语言控制终端执行命令

运行: python3 terminal_agent_demo.py
"""

import subprocess
import json
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# ============================================
# 配置区
# ============================================
# 通用LLM配置 - 用于意图分析、问答等
LLM_CONFIG = {
    "model": "gpt-4.1-mini",
    "base_url": "https://sdwfger.edu.kg/v1",
    "api_key": "sk-lCVcio0vmI5U16K1ru9gdJ7ZsszU3lsKnUurlNjhROjWLwxU",
    "temperature": 0,
}

# 代码生成专用LLM配置 - 用于生成命令和代码
LLM_CONFIG2 = {
    "model": "claude-3-5-sonnet",  # 使用Claude作为代码生成模型
    "base_url": "https://sdwfger.edu.kg/v1",
    "api_key": "sk-lCVcio0vmI5U16K1ru9gdJ7ZsszU3lsKnUurlNjhROjWLwxU",
    "temperature": 0,
}


# ============================================
# 数据结构定义
# ============================================
class AgentState(TypedDict):
    """智能体状态"""
    user_input: str
    intent: Literal["terminal_command", "multi_step_command", "question", "unknown"]
    command: str
    commands: list  # 多步骤命令列表
    command_output: str
    command_outputs: list  # 多个命令的输出
    response: str
    error: str
    needs_file_creation: bool  # 是否需要创建文件
    file_path: str  # 要创建的文件路径
    file_content: str  # 文件内容


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
    """
    安全地执行终端命令
    返回: {"success": bool, "output": str, "error": str}
    """
    # 安全检查 - 禁止危险命令
    dangerous_commands = ["rm -rf", "sudo", "chmod", "format", "del /f"]
    for dangerous in dangerous_commands:
        if dangerous in command.lower():
            return {
                "success": False,
                "output": "",
                "error": f"拒绝执行危险命令: {command}"
            }

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": "命令执行超时"
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": f"执行失败: {str(e)}"
        }


# ============================================
# 节点函数定义
# ============================================

def intent_analyzer(state: AgentState) -> dict:
    """
    分析用户意图: 是要执行终端命令还是问问题
    """
    user_input = state["user_input"]

    prompt = f"""分析用户意图,只返回一个词: 'terminal_command', 'multi_step_command' 或 'question'

用户输入: {user_input}

判断规则:
- 如果用户想执行系统命令、查看文件、运行程序 -> terminal_command
- 如果用户需要创建文件并执行、或者需要多个步骤完成任务 -> multi_step_command
- 如果用户在问问题、寻求解释、需要建议 -> question

意图:"""

    result = llm.invoke([HumanMessage(content=prompt)])
    intent = result.content.strip().lower()

    if intent not in ["terminal_command", "multi_step_command", "question"]:
        intent = "unknown"

    print(f"\n[意图分析] {user_input}")
    print(f"           意图: {intent}")

    return {"intent": intent}


def command_generator(state: AgentState) -> dict:
    """
    将用户的自然语言转换为终端命令
    """
    user_input = state["user_input"]

    prompt = f"""将用户的自然语言请求转换为终端命令。只返回命令本身,不要解释。

用户请求: {user_input}

示例:
- "列出当前目录的所有文件" -> ls -la
- "查看Python版本" -> python3 --version
- "显示当前路径" -> pwd
- "创建一个名为test.txt的文件" -> touch test.txt

终端命令:"""

    result = llm_code.invoke([HumanMessage(content=prompt)])  # 使用代码生成LLM
    command = result.content.strip()

    print(f"[命令生成] {command}")

    return {"command": command}


def multi_step_planner(state: AgentState) -> dict:
    """
    将复杂任务分解为多个步骤，并识别是否需要创建文件（使用代码生成LLM）
    """
    user_input = state["user_input"]

    prompt = f"""分析用户请求，返回JSON格式的执行计划。

用户请求: {user_input}

你需要返回一个JSON对象，包含:
{{
  "needs_file_creation": true/false,  # 是否需要创建文件
  "file_path": "文件路径",  # 如果需要创建文件
  "file_content": "文件内容",  # 如果需要创建文件
  "commands": ["命令1", "命令2"]  # 要执行的终端命令列表
}}

示例1:
输入: "创建一个Python文件hello.py，内容是print('Hello World')，然后执行它"
输出:
{{
  "needs_file_creation": true,
  "file_path": "hello.py",
  "file_content": "print('Hello World')",
  "commands": ["python3 hello.py"]
}}

示例2:
输入: "查看当前目录然后显示Python版本"
输出:
{{
  "needs_file_creation": false,
  "file_path": "",
  "file_content": "",
  "commands": ["pwd", "python3 --version"]
}}

只返回JSON，不要其他解释:"""

    result = llm_code.invoke([HumanMessage(content=prompt)])  # 使用代码生成LLM
    plan_text = result.content.strip()
    
    # 提取JSON内容
    if "```json" in plan_text:
        plan_text = plan_text.split("```json")[1].split("```")[0].strip()
    elif "```" in plan_text:
        plan_text = plan_text.split("```")[1].split("```")[0].strip()
    
    try:
        plan = json.loads(plan_text)
        print(f"[多步骤规划] 需要创建文件: {plan.get('needs_file_creation', False)}")
        print(f"            命令数量: {len(plan.get('commands', []))}")
        
        return {
            "needs_file_creation": plan.get("needs_file_creation", False),
            "file_path": plan.get("file_path", ""),
            "file_content": plan.get("file_content", ""),
            "commands": plan.get("commands", [])
        }
    except json.JSONDecodeError:
        print(f"[多步骤规划] JSON解析失败，使用默认值")
        return {
            "needs_file_creation": False,
            "file_path": "",
            "file_content": "",
            "commands": [],
            "error": "无法解析执行计划"
        }


def file_creator(state: AgentState) -> dict:
    """
    创建文件
    """
    file_path = state["file_path"]
    file_content = state["file_content"]
    
    print(f"[文件创建] 创建文件: {file_path}")
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
        print(f"[文件创建] 成功创建文件: {file_path}")
        return {"error": ""}
    except Exception as e:
        error_msg = f"文件创建失败: {str(e)}"
        print(f"[文件创建] {error_msg}")
        return {"error": error_msg}


def multi_command_executor(state: AgentState) -> dict:
    """
    执行多个终端命令
    """
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
            print(f"[多命令执行] 第{idx}个命令执行成功")
        else:
            print(f"[多命令执行] 第{idx}个命令执行失败: {result['error']}")
            # 继续执行后续命令，不中断
    
    return {"command_outputs": outputs}


def command_executor(state: AgentState) -> dict:
    """
    执行终端命令
    """
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
    """
    格式化最终响应
    """
    if state["intent"] == "terminal_command":
        if state.get("error"):
            response = f"命令执行失败\n命令: {state['command']}\n错误: {state['error']}"
        else:
            response = f"命令执行成功\n命令: {state['command']}\n输出:\n{state['command_output']}"
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
    else:
        response = "抱歉,我无法处理这个请求。"

    print(f"[格式化响应] 完成")

    return {"response": response}


def question_answerer(state: AgentState) -> dict:
    """
    回答用户问题
    """
    user_input = state["user_input"]

    prompt = f"""简要回答用户问题:

{user_input}

回答:"""

    result = llm.invoke([HumanMessage(content=prompt)])
    response = result.content

    print(f"[问题回答] 生成回答")

    return {"response": response}


# ============================================
# 路由函数
# ============================================

def route_by_intent(state: AgentState) -> str:
    """根据意图路由到不同处理节点"""
    intent = state["intent"]
    if intent == "terminal_command":
        return "generate_command"
    elif intent == "multi_step_command":
        return "plan_steps"
    elif intent == "question":
        return "answer_question"
    else:
        return "format_response"


def route_after_planning(state: AgentState) -> str:
    """规划后的路由: 决定是否需要创建文件"""
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

    # 添加节点
    workflow.add_node("analyze_intent", intent_analyzer)
    workflow.add_node("generate_command", command_generator)
    workflow.add_node("execute_command", command_executor)
    workflow.add_node("plan_steps", multi_step_planner)
    workflow.add_node("create_file", file_creator)
    workflow.add_node("execute_multi_commands", multi_command_executor)
    workflow.add_node("format_response", response_formatter)
    workflow.add_node("answer_question", question_answerer)

    # 设置入口
    workflow.set_entry_point("analyze_intent")

    # 条件路由: 根据意图选择路径
    workflow.add_conditional_edges(
        "analyze_intent",
        route_by_intent,
        {
            "generate_command": "generate_command",
            "plan_steps": "plan_steps",
            "answer_question": "answer_question",
            "format_response": "format_response"
        }
    )

    # 单步命令路径
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
    
    # 结束路径
    workflow.add_edge("format_response", END)
    workflow.add_edge("answer_question", END)

    return workflow.compile()


# ============================================
# 主函数
# ============================================

def main():
    """运行AI终端控制智能体Demo"""

    agent = build_agent()

    test_inputs = [
        "显示当前目录的路径",
        "列出当前目录的所有文件",
        "查看Python版本",
        "什么是LangGraph?",
        "创建一个Python文件hello.py，内容是print('Hello World')，然后执行它",
    ]

    print("=" * 80)
    print("AI智能体终端控制工具Demo")
    print("演示AI Agent如何理解自然语言并执行终端命令")
    print("=" * 80)

    for user_input in test_inputs:
        print(f"\n{'=' * 80}")
        print(f"用户输入: {user_input}")
        print(f"{'-' * 80}")

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
            "file_content": ""
        }

        result = agent.invoke(initial_state)

        print(f"{'-' * 80}")
        print(f"最终响应:\n{result['response']}")
        print()


if __name__ == "__main__":
    main()
