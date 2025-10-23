"""
智能体类型定义模块
使用 dataclass 提供类型安全和结构化的状态管理
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, TypedDict, Literal


class Intent(Enum):
    """意图枚举 - 提供类型安全的意图标识"""

    # 命令执行类
    TERMINAL_COMMAND = "terminal_command"
    MULTI_STEP_COMMAND = "multi_step_command"

    # Git 操作类
    GIT_COMMIT = "git_commit"
    AUTO_COMMIT = "auto_commit"
    FULL_GIT_WORKFLOW = "full_git_workflow"
    GIT_PULL = "git_pull"
    GIT_PUSH = "git_push"

    # MCP 工具调用
    MCP_TOOL_CALL = "mcp_tool_call"

    # 问答类
    QUESTION = "question"

    # 待办管理类
    ADD_TODO = "add_todo"
    QUERY_TODO = "query_todo"

    # 数据转换类
    DATA_CONVERSION = "data_conversion"

    # 环境诊断类
    ENVIRONMENT_DIAGNOSTIC = "environment_diagnostic"

    # 未知类型
    UNKNOWN = "unknown"


@dataclass
class ExecutionContext:
    """执行上下文 - 基础信息"""
    user_input: str
    intent: Intent = Intent.UNKNOWN
    original_input: str = ""


@dataclass
class CommandResult:
    """命令执行结果"""
    commands: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    error: str = ""

    # 单命令兼容字段(向后兼容)
    command: str = ""
    command_output: str = ""


@dataclass
class FileContext:
    """文件上下文 - 文件引用相关"""
    referenced_files: List[str] = field(default_factory=list)
    file_contents: Dict[str, str] = field(default_factory=dict)

    # 文件创建相关
    needs_file_creation: bool = False
    file_path: str = ""
    file_content: str = ""


@dataclass
class MCPContext:
    """MCP 工具调用上下文"""
    tool: str = ""
    params: Dict = field(default_factory=dict)
    result: str = ""


@dataclass
class TodoData:
    """待办事项数据"""
    action: str = ""  # add/query/search
    date: str = ""
    time: str = ""
    content: str = ""
    result: str = ""


@dataclass
class DataConversionData:
    """数据转换数据"""
    conversion_type: str = ""
    source_format: str = ""
    target_format: str = ""
    result: str = ""


@dataclass
class GitData:
    """Git 操作数据"""
    # Git 自动提交相关
    add_success: bool = False
    files_count: int = 0
    commit_message_generated: bool = False
    commit_message: str = ""
    file_stats: str = ""
    commit_success: bool = False
    commit_hash: str = ""

    # Git pull/push 相关
    pull_success: bool = False
    pull_has_updates: bool = False
    push_success: bool = False
    push_branch: str = ""


@dataclass
class AgentState:
    """
    智能体状态 - 重构版本

    使用 dataclass 提供:
    1. 类型安全
    2. 结构化数据
    3. 可选字段默认值
    4. 更好的可维护性
    """
    # 核心上下文(必需)
    context: ExecutionContext

    # 响应和错误
    response: str = ""
    error: str = ""

    # 对话历史
    chat_history: List = field(default_factory=list)

    # 子模块上下文(按需创建)
    command_result: Optional[CommandResult] = None
    file_context: Optional[FileContext] = None
    mcp_context: Optional[MCPContext] = None
    todo_data: Optional[TodoData] = None
    conversion_data: Optional[DataConversionData] = None
    git_data: Optional[GitData] = None

    # 环境诊断结果
    diagnostic_result: str = ""

    def to_dict(self) -> Dict:
        """
        转换为字典格式(向后兼容旧的 TypedDict)

        Returns:
            扁平化的字典,匹配旧的 AgentState TypedDict 结构
        """
        # 基础字段
        result = {
            "user_input": self.context.user_input,
            "intent": self.context.intent.value,
            "original_input": self.context.original_input,
            "response": self.response,
            "error": self.error,
            "chat_history": self.chat_history,
            "diagnostic_result": self.diagnostic_result,
        }

        # 命令结果
        if self.command_result:
            result.update({
                "command": self.command_result.command,
                "commands": self.command_result.commands,
                "command_output": self.command_result.command_output,
                "command_outputs": self.command_result.outputs,
            })
        else:
            result.update({
                "command": "",
                "commands": [],
                "command_output": "",
                "command_outputs": [],
            })

        # 文件上下文
        if self.file_context:
            result.update({
                "needs_file_creation": self.file_context.needs_file_creation,
                "file_path": self.file_context.file_path,
                "file_content": self.file_context.file_content,
                "referenced_files": self.file_context.referenced_files,
                "file_contents": self.file_context.file_contents,
            })
        else:
            result.update({
                "needs_file_creation": False,
                "file_path": "",
                "file_content": "",
                "referenced_files": [],
                "file_contents": {},
            })

        # MCP 上下文
        if self.mcp_context:
            result.update({
                "mcp_tool": self.mcp_context.tool,
                "mcp_params": self.mcp_context.params,
                "mcp_result": self.mcp_context.result,
            })
        else:
            result.update({
                "mcp_tool": "",
                "mcp_params": {},
                "mcp_result": "",
            })

        # 待办数据
        if self.todo_data:
            result.update({
                "todo_action": self.todo_data.action,
                "todo_date": self.todo_data.date,
                "todo_time": self.todo_data.time,
                "todo_content": self.todo_data.content,
                "todo_result": self.todo_data.result,
            })
        else:
            result.update({
                "todo_action": "",
                "todo_date": "",
                "todo_time": "",
                "todo_content": "",
                "todo_result": "",
            })

        # 数据转换数据
        if self.conversion_data:
            result.update({
                "data_conversion_type": self.conversion_data.conversion_type,
                "source_format": self.conversion_data.source_format,
                "target_format": self.conversion_data.target_format,
                "conversion_result": self.conversion_data.result,
            })
        else:
            result.update({
                "data_conversion_type": "",
                "source_format": "",
                "target_format": "",
                "conversion_result": "",
            })

        # Git 数据
        if self.git_data:
            result.update({
                "git_add_success": self.git_data.add_success,
                "git_files_count": self.git_data.files_count,
                "git_commit_message_generated": self.git_data.commit_message_generated,
                "git_commit_message": self.git_data.commit_message,
                "git_file_stats": self.git_data.file_stats,
                "git_commit_success": self.git_data.commit_success,
                "git_commit_hash": self.git_data.commit_hash,
                "git_pull_success": self.git_data.pull_success,
                "git_pull_has_updates": self.git_data.pull_has_updates,
                "git_push_success": self.git_data.push_success,
                "git_push_branch": self.git_data.push_branch,
            })
        else:
            result.update({
                "git_add_success": False,
                "git_files_count": 0,
                "git_commit_message_generated": False,
                "git_commit_message": "",
                "git_file_stats": "",
                "git_commit_success": False,
                "git_commit_hash": "",
                "git_pull_success": False,
                "git_pull_has_updates": False,
                "git_push_success": False,
                "git_push_branch": "",
            })

        return result

    @classmethod
    def from_dict(cls, data: Dict) -> 'AgentState':
        """
        从字典创建 AgentState(向后兼容)

        Args:
            data: 旧格式的字典

        Returns:
            新的 AgentState 实例
        """
        # 解析 intent
        intent_str = data.get("intent", "unknown")
        try:
            intent = Intent(intent_str)
        except ValueError:
            intent = Intent.UNKNOWN

        # 创建执行上下文
        context = ExecutionContext(
            user_input=data.get("user_input", ""),
            intent=intent,
            original_input=data.get("original_input", ""),
        )

        # 创建命令结果(如果存在)
        command_result = None
        if data.get("commands") or data.get("command"):
            command_result = CommandResult(
                commands=data.get("commands", []),
                outputs=data.get("command_outputs", []),
                error=data.get("error", ""),
                command=data.get("command", ""),
                command_output=data.get("command_output", ""),
            )

        # 创建文件上下文(如果存在)
        file_context = None
        if data.get("referenced_files") or data.get("needs_file_creation"):
            file_context = FileContext(
                referenced_files=data.get("referenced_files", []),
                file_contents=data.get("file_contents", {}),
                needs_file_creation=data.get("needs_file_creation", False),
                file_path=data.get("file_path", ""),
                file_content=data.get("file_content", ""),
            )

        # 创建 MCP 上下文(如果存在)
        mcp_context = None
        if data.get("mcp_tool"):
            mcp_context = MCPContext(
                tool=data.get("mcp_tool", ""),
                params=data.get("mcp_params", {}),
                result=data.get("mcp_result", ""),
            )

        # 创建待办数据(如果存在)
        todo_data = None
        if data.get("todo_action"):
            todo_data = TodoData(
                action=data.get("todo_action", ""),
                date=data.get("todo_date", ""),
                time=data.get("todo_time", ""),
                content=data.get("todo_content", ""),
                result=data.get("todo_result", ""),
            )

        # 创建数据转换数据(如果存在)
        conversion_data = None
        if data.get("data_conversion_type"):
            conversion_data = DataConversionData(
                conversion_type=data.get("data_conversion_type", ""),
                source_format=data.get("source_format", ""),
                target_format=data.get("target_format", ""),
                result=data.get("conversion_result", ""),
            )

        # 创建 Git 数据(如果存在)
        git_data = None
        if any(k.startswith("git_") for k in data.keys()):
            git_data = GitData(
                add_success=data.get("git_add_success", False),
                files_count=data.get("git_files_count", 0),
                commit_message_generated=data.get("git_commit_message_generated", False),
                commit_message=data.get("git_commit_message", ""),
                file_stats=data.get("git_file_stats", ""),
                commit_success=data.get("git_commit_success", False),
                commit_hash=data.get("git_commit_hash", ""),
                pull_success=data.get("git_pull_success", False),
                pull_has_updates=data.get("git_pull_has_updates", False),
                push_success=data.get("git_push_success", False),
                push_branch=data.get("git_push_branch", ""),
            )

        return cls(
            context=context,
            response=data.get("response", ""),
            error=data.get("error", ""),
            chat_history=data.get("chat_history", []),
            command_result=command_result,
            file_context=file_context,
            mcp_context=mcp_context,
            todo_data=todo_data,
            conversion_data=conversion_data,
            git_data=git_data,
            diagnostic_result=data.get("diagnostic_result", ""),
        )


def create_initial_state(user_input: str) -> AgentState:
    """
    工厂函数 - 创建初始状态

    这是创建 AgentState 的唯一入口,确保一致性

    Args:
        user_input: 用户输入

    Returns:
        初始化的 AgentState 实例
    """
    return AgentState(
        context=ExecutionContext(user_input=user_input)
    )


# ============================================
# TypedDict 版本 - 用于 LangGraph
# ============================================

class AgentStateDict(TypedDict):
    """
    AgentState 的 TypedDict 版本

    LangGraph 需要 TypedDict 来定义状态图
    这个版本与 AgentState dataclass 的 to_dict() 输出格式一致
    """
    # 基础字段
    user_input: str
    intent: str
    original_input: str
    response: str
    error: str
    chat_history: list
    diagnostic_result: str

    # 命令结果
    command: str
    commands: list
    command_output: str
    command_outputs: list

    # 文件上下文
    needs_file_creation: bool
    file_path: str
    file_content: str
    referenced_files: list
    file_contents: dict

    # MCP 上下文
    mcp_tool: str
    mcp_params: dict
    mcp_result: str

    # 待办数据
    todo_action: str
    todo_date: str
    todo_time: str
    todo_content: str
    todo_result: str

    # 数据转换数据
    data_conversion_type: str
    source_format: str
    target_format: str
    conversion_result: str

    # Git 数据
    git_add_success: bool
    git_files_count: int
    git_commit_message_generated: bool
    git_commit_message: str
    git_file_stats: str
    git_commit_success: bool
    git_commit_hash: str
    git_pull_success: bool
    git_pull_has_updates: bool
    git_push_success: bool
    git_push_branch: str

