"""
知识化项目 - LangChain Tool 封装

一个工具：knowledge_project
入参(JSON 字符串)：
  - action: init|update|export （init=全量构建，update=增量/当前同init，export=仅根据现有 kb.json 导出卡片与索引）
  - work_dir: 工作目录（可选，默认当前）

输出：人类可读的执行结果与生成目录。
"""

import json
import os
from pathlib import Path
from typing import Dict, Any
from langchain_core.tools import Tool

from .builder import build_knowledge_base
from .exporters import export_kb


def knowledge_project_tool_func(input_str: str) -> str:
    try:
        work_dir = os.getcwd()
        action = "init"

        if input_str.strip():
            try:
                data = json.loads(input_str)
                work_dir = data.get("work_dir", work_dir)
                action = data.get("action", action)
            except json.JSONDecodeError:
                pass

        # kb 路径
        base = Path(work_dir) / "knowledge"
        kb_path = base / "kb.json"

        if action in ("init", "update"):
            kb = build_knowledge_base(work_dir)
            out_dir = export_kb(work_dir, kb)
            return f"""🎉 知识库已构建

📁 目录: {out_dir}
📄 清单: {kb_path}
📊 统计: items={kb['stats']['items']} relations={kb['stats']['relations']} files={kb['stats']['files_scanned']}

下次可执行: action=export 仅重新生成索引/卡片
"""

        elif action == "export":
            if not kb_path.exists():
                return "❌ 未找到 knowledge/kb.json，请先执行 action=init 进行构建"
            # 直接读取并导出
            try:
                kb = json.loads(kb_path.read_text(encoding="utf-8"))
            except Exception as e:
                return f"❌ 读取 kb.json 失败: {e}"
            out_dir = export_kb(work_dir, kb)
            return f"""✅ 导出完成

📁 目录: {out_dir}
📄 清单: {kb_path}
"""

        else:
            return "❌ 未知 action，支持: init/update/export"

    except Exception as e:
        return f"❌ 知识库构建失败: {str(e)}"


knowledge_project_tool = Tool(
    name="knowledge_project",
    description="""自动知识化项目：扫描代码与文档，生成知识库（knowledge/）。支持 action=init|update|export。""",
    func=knowledge_project_tool_func,
)

knowledge_project_tools = [knowledge_project_tool]

