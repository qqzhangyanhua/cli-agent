"""
AI智能体终端控制工具 - MCP文件系统集成版本
支持对话功能、记忆功能和文件系统访问

运行: python3 terminal_agent_mcp.py
"""

import subprocess
import json
import os
from typing import TypedDict, Literal, List
from datetime import datetime
from pathlib import Path
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

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
    "model": "claude-3-5-sonnet",
    "base_url": "https://sdwfger.edu.kg/v1",
    "api_key": "sk-",
    "temperature": 0,
}

# 文件系统访问配置
FILESYSTEM_CONFIG = {
    "allowed_dirs": [
        "/Users/zhangyanhua/Desktop/AI/tushare/quantification/example",
        "/Users/zhangyanhua/Desktop/AI/tushare/quantification"
    ],
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "allowed_extensions": [".txt", ".py", ".json", ".csv", ".md", ".log", ".sh"]
}


# ============================================
# 数据结构定义
# ============================================
class AgentState(TypedDict):
    """智能体状态"""
    user_input: str
    intent: Literal["terminal_command", "multi_step_command", "file_operation", "question", "unknown"]
    command: str
    commands: list
    command_output: str
    command_outputs: list
    response: str
    error: str
    needs_file_creation: bool
    file_path: str
    file_content: str
    chat_history: list
    # MCP相关字段
    file_operation: str  # read, write, list, search
    file_params: dict  # 文件操作参数
    file_result: str  # 文件操作结果


# ============================================
# 文件系统工具类 (MCP-like)
# ============================================
class FileSystemTools:
    """文件系统访问工具（模拟MCP filesystem服务器）"""
    
    def __init__(self, allowed_dirs, max_file_size, allowed_extensions):
        self.allowed_dirs = [Path(d).resolve() for d in allowed_dirs]
        self.max_file_size = max_file_size
        self.allowed_extensions = allowed_extensions
    
    def _is_path_allowed(self, file_path: str) -> bool:
        """检查路径是否在允许的目录内"""
        try:
            path = Path(file_path).resolve()
            return any(path.is_relative_to(allowed_dir) for allowed_dir in self.allowed_dirs)
        except Exception:
            return False
    
    def _check_file_size(self, file_path: str) -> bool:
        """检查文件大小"""
        try:
            return os.path.getsize(file_path) <= self.max_file_size
        except Exception:
            return False
    
    def _check_extension(self, file_path: str) -> bool:
        """检查文件扩展名"""
        ext = Path(file_path).suffix.lower()
        return ext in self.allowed_extensions or ext == ""
    
    def read_file(self, file_path: str) -> dict:
        """读取文件内容"""
        try:
            if not self._is_path_allowed(file_path):
                return {
                    "success": False,
                    "error": f"拒绝访问: 路径不在允许的目录内"
                }
            
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": f"文件不存在: {file_path}"
                }
            
            if not self._check_file_size(file_path):
                return {
                    "success": False,
                    "error": f"文件太大（超过{self.max_file_size // 1024 // 1024}MB）"
                }
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "success": True,
                "content": content,
                "size": len(content),
                "lines": content.count('\n') + 1
            }
        
        except UnicodeDecodeError:
            return {
                "success": False,
                "error": "无法读取文件（可能是二进制文件）"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"读取失败: {str(e)}"
            }
    
    def write_file(self, file_path: str, content: str, mode: str = "w") -> dict:
        """写入文件"""
        try:
            if not self._is_path_allowed(file_path):
                return {
                    "success": False,
                    "error": f"拒绝访问: 路径不在允许的目录内"
                }
            
            if not self._check_extension(file_path):
                return {
                    "success": False,
                    "error": f"不允许的文件类型"
                }
            
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
            
            with open(file_path, mode, encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "path": file_path,
                "size": len(content),
                "lines": content.count('\n') + 1
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"写入失败: {str(e)}"
            }
    
    def list_directory(self, dir_path: str, pattern: str = "*") -> dict:
        """列出目录内容"""
        try:
            if not self._is_path_allowed(dir_path):
                return {
                    "success": False,
                    "error": f"拒绝访问: 路径不在允许的目录内"
                }
            
            if not os.path.exists(dir_path):
                return {
                    "success": False,
                    "error": f"目录不存在: {dir_path}"
                }
            
            if not os.path.isdir(dir_path):
                return {
                    "success": False,
                    "error": f"不是目录: {dir_path}"
                }
            
            path = Path(dir_path)
            files = []
            dirs = []
            
            for item in path.glob(pattern):
                if item.is_file():
                    files.append({
                        "name": item.name,
                        "path": str(item),
                        "size": item.stat().st_size,
                        "modified": datetime.fromtimestamp(item.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    })
                elif item.is_dir():
                    dirs.append({
                        "name": item.name,
                        "path": str(item)
                    })
            
            return {
                "success": True,
                "path": dir_path,
                "files": files,
                "directories": dirs,
                "total_files": len(files),
                "total_dirs": len(dirs)
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"列出目录失败: {str(e)}"
            }
    
    def search_files(self, dir_path: str, pattern: str, content_search: str = None) -> dict:
        """搜索文件"""
        try:
            if not self._is_path_allowed(dir_path):
                return {
                    "success": False,
                    "error": f"拒绝访问: 路径不在允许的目录内"
                }
            
            path = Path(dir_path)
            matches = []
            
            # 按文件名搜索
            for item in path.rglob(pattern):
                if item.is_file() and self._is_path_allowed(str(item)):
                    match_info = {
                        "name": item.name,
                        "path": str(item),
                        "size": item.stat().st_size
                    }
                    
                    # 如果需要内容搜索
                    if content_search and self._check_extension(str(item)):
                        try:
                            with open(item, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if content_search.lower() in content.lower():
                                    match_info["matched_content"] = True
                                    matches.append(match_info)
                        except:
                            pass
                    else:
                        matches.append(match_info)
            
            return {
                "success": True,
                "matches": matches,
                "total": len(matches)
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"搜索失败: {str(e)}"
            }


# ============================================
# 全局实例
# ============================================
fs_tools = FileSystemTools(
    FILESYSTEM_CONFIG["allowed_dirs"],
    FILESYSTEM_CONFIG["max_file_size"],
    FILESYSTEM_CONFIG["allowed_extensions"]
)


class ConversationMemory:
    """对话记忆管理"""
    def __init__(self, max_history=10):
        self.history: List[dict] = []
        self.max_history = max_history
        self.command_history: List[dict] = []
        self.file_operations: List[dict] = []  # 文件操作历史
    
    def add_interaction(self, user_input: str, agent_response: str, intent: str):
        """添加一次交互到历史"""
        self.history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": user_input,
            "agent": agent_response,
            "intent": intent
        })
        
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
    
    def add_file_operation(self, operation: str, path: str, success: bool):
        """记录文件操作历史"""
        self.file_operations.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operation": operation,
            "path": path,
            "success": success
        })
        
        if len(self.file_operations) > 20:
            self.file_operations.pop(0)
    
    def get_context_string(self) -> str:
        """获取对话上下文字符串"""
        if not self.history:
            return "这是我们的第一次对话。"
        
        context = "对话历史:\n"
        for idx, interaction in enumerate(self.history[-5:], 1):
            context += f"{idx}. 用户: {interaction['user']}\n"
            context += f"   助手: {interaction['agent'][:100]}...\n"
        
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
    
    def get_recent_file_ops(self, n=3) -> str:
        """获取最近的文件操作"""
        if not self.file_operations:
            return "暂无文件操作历史。"
        
        recent = self.file_operations[-n:]
        result = "最近的文件操作:\n"
        for op in recent:
            status = "✅" if op["success"] else "❌"
            result += f"{status} {op['operation']}: {op['path']}\n"
        
        return result
    
    def clear(self):
        """清空记忆"""
        self.history.clear()
        self.command_history.clear()
        self.file_operations.clear()


memory = ConversationMemory(max_history=10)


# ============================================
# 初始化 LLM
# ============================================
llm = ChatOpenAI(
    model=LLM_CONFIG["model"],
    base_url=LLM_CONFIG["base_url"],
    api_key=LLM_CONFIG["api_key"],
    temperature=LLM_CONFIG["temperature"],
    default_headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
)

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
    """分析用户意图（带文件操作识别）"""
    user_input = state["user_input"]
    context = memory.get_context_string()

    prompt = f"""你是一个智能终端助手。根据用户输入和对话历史，分析用户意图。

{context}

当前用户输入: {user_input}

判断规则:
- 如果用户想执行系统命令、查看文件、运行程序 -> terminal_command
- 如果用户需要创建文件并执行、或者需要多个步骤完成任务 -> multi_step_command
- 如果用户想读取文件内容、写入文件、列出目录、搜索文件 -> file_operation
- 如果用户在问问题、寻求解释、需要建议、或者引用之前的对话 -> question

只返回一个词: 'terminal_command', 'multi_step_command', 'file_operation' 或 'question'

意图:"""

    result = llm.invoke([HumanMessage(content=prompt)])
    intent = result.content.strip().lower()

    if intent not in ["terminal_command", "multi_step_command", "file_operation", "question"]:
        intent = "question"

    print(f"\n[意图分析] {user_input[:50]}...")
    print(f"           使用模型: {LLM_CONFIG['model']}")
    print(f"           意图: {intent}")

    return {"intent": intent}


def file_operation_planner(state: AgentState) -> dict:
    """规划文件操作（新增节点）"""
    user_input = state["user_input"]
    recent_ops = memory.get_recent_file_ops()

    prompt = f"""分析用户的文件操作请求，返回JSON格式的操作计划。

{recent_ops}

用户请求: {user_input}

返回JSON对象:
{{
  "operation": "read|write|list|search",
  "file_path": "文件或目录路径",
  "content": "写入的内容（仅write操作）",
  "pattern": "搜索模式（仅search操作）",
  "mode": "w或a（仅write操作，w=覆盖,a=追加）"
}}

示例1:
输入: "读取README.md文件"
输出:
{{
  "operation": "read",
  "file_path": "README.md"
}}

示例2:
输入: "在result.txt中写入'完成'"
输出:
{{
  "operation": "write",
  "file_path": "result.txt",
  "content": "完成",
  "mode": "w"
}}

示例3:
输入: "列出当前目录的所有文件"
输出:
{{
  "operation": "list",
  "file_path": "."
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
        print(f"[文件操作规划] 使用模型: {LLM_CONFIG2['model']}")
        print(f"              操作类型: {plan.get('operation', 'unknown')}")
        print(f"              目标路径: {plan.get('file_path', 'N/A')}")
        
        return {
            "file_operation": plan.get("operation", ""),
            "file_params": plan
        }
    except json.JSONDecodeError:
        print(f"[文件操作规划] JSON解析失败")
        return {
            "file_operation": "",
            "file_params": {},
            "error": "无法解析文件操作计划"
        }


def file_operation_executor(state: AgentState) -> dict:
    """执行文件操作（新增节点）"""
    operation = state["file_operation"]
    params = state["file_params"]
    
    print(f"[文件操作执行] 操作: {operation}")
    
    try:
        if operation == "read":
            result = fs_tools.read_file(params["file_path"])
            memory.add_file_operation("read", params["file_path"], result["success"])
            
        elif operation == "write":
            result = fs_tools.write_file(
                params["file_path"],
                params.get("content", ""),
                params.get("mode", "w")
            )
            memory.add_file_operation("write", params["file_path"], result["success"])
            
        elif operation == "list":
            result = fs_tools.list_directory(
                params["file_path"],
                params.get("pattern", "*")
            )
            memory.add_file_operation("list", params["file_path"], result["success"])
            
        elif operation == "search":
            result = fs_tools.search_files(
                params.get("dir_path", "."),
                params.get("pattern", "*"),
                params.get("content_search")
            )
            memory.add_file_operation("search", params.get("dir_path", "."), result["success"])
            
        else:
            result = {
                "success": False,
                "error": f"未知的操作类型: {operation}"
            }
        
        if result["success"]:
            print(f"[文件操作执行] ✅ 成功")
        else:
            print(f"[文件操作执行] ❌ 失败: {result.get('error', 'Unknown error')}")
        
        return {"file_result": json.dumps(result, ensure_ascii=False)}
    
    except Exception as e:
        error_msg = f"文件操作执行失败: {str(e)}"
        print(f"[文件操作执行] ❌ {error_msg}")
        return {
            "file_result": json.dumps({"success": False, "error": error_msg}, ensure_ascii=False)
        }


# 继续后面的节点函数...
# (由于字符限制，我将在第二部分继续)
