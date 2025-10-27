"""
文件引用处理节点
解析 @ 语法并读取文件内容
"""

from src.core.agent_config import AgentState
from src.mcp.mcp_manager import mcp_manager
from src.ui.file_reference_parser import parse_file_references, file_parser


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
