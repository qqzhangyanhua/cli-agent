"""
项目管理工具模块
提供智能项目检测、启动、打包和诊断功能
"""

# 导出所有类
from src.tools.project_manager.detector import ProjectDetector
from src.tools.project_manager.analyzer import CommandAnalyzer
from src.tools.project_manager.process_manager import ProcessManager, process_manager
from src.tools.project_manager.executor import SmartExecutor

# 导出工具函数
from src.tools.project_manager.tools import (
    start_project_tool_func,
    build_project_tool_func,
    stop_project_tool_func,
    diagnose_project_tool_func,
    start_project_tool,
    build_project_tool,
    stop_project_tool,
    diagnose_project_tool,
    project_manager_tools
)

__all__ = [
    # 类
    "ProjectDetector",
    "CommandAnalyzer",
    "ProcessManager",
    "SmartExecutor",

    # 全局单例
    "process_manager",

    # 工具函数
    "start_project_tool_func",
    "build_project_tool_func",
    "stop_project_tool_func",
    "diagnose_project_tool_func",

    # LangChain Tools
    "start_project_tool",
    "build_project_tool",
    "stop_project_tool",
    "diagnose_project_tool",
    "project_manager_tools",
]
