"""
自动知识化项目 - 工具导出

提供对项目进行“知识化”的最小可用实现：
- 扫描代码与文档，抽取结构化知识项（文件、类、函数、配置等）
- 生成知识库目录 knowledge/（kb.json、知识卡片、索引）
- 支持 action: init/update/export 三种动作（当前 init=全量构建，update=与 init 等价，export=导出知识卡/索引）

仅使用标准库实现，避免外部依赖。
"""

from .tools import (
    knowledge_project_tool_func,
    knowledge_project_tool,
    knowledge_project_tools,
)

__all__ = [
    "knowledge_project_tool_func",
    "knowledge_project_tool",
    "knowledge_project_tools",
]

