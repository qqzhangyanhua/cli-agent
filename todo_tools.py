"""
待办事项管理工具 - LangChain Tool封装
将待办管理功能封装为LangChain工具，让LLM自主调用
"""

from langchain_core.tools import Tool
from datetime import datetime, timedelta
from typing import Dict, List
import json

from todo_manager import todo_manager


def add_todo_tool_func(input_str: str) -> str:
    """
    添加待办事项

    Args:
        input_str: JSON格式的输入，包含 date, time, content
        例如: {"date": "2025-10-22", "time": "18:00", "content": "给成龙打电话"}

    Returns:
        操作结果的文本描述
    """
    try:
        # 解析输入
        data = json.loads(input_str)
        date = data.get("date", "")
        time = data.get("time", "")
        content = data.get("content", "")

        if not date or not content:
            return "❌ 错误：必须提供日期(date)和内容(content)"

        # 验证日期格式
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return f"❌ 日期格式无效: {date}，请使用 YYYY-MM-DD 格式"

        # 验证时间格式（如果提供）
        if time:
            try:
                datetime.strptime(time, "%H:%M")
            except ValueError:
                return f"⚠️  时间格式无效: {time}，已忽略时间部分"

        # 添加待办
        todo_item = todo_manager.add_todo(date, time, content)

        if todo_item:
            result = f"✅ 待办已添加！\n"
            result += f"📅 日期: {date}\n"
            if time:
                result += f"⏰ 时间: {time}\n"
            result += f"📝 内容: {content}"
            return result
        else:
            return "❌ 添加待办失败"

    except json.JSONDecodeError as e:
        return f"❌ JSON解析失败: {str(e)}\n请使用正确的JSON格式"
    except Exception as e:
        return f"❌ 添加待办时发生错误: {str(e)}"


def query_todo_tool_func(input_str: str) -> str:
    """
    查询待办事项

    Args:
        input_str: JSON格式的查询条件
        例如: {"type": "today"} 或 {"type": "date", "date": "2025-10-22"}
              或 {"type": "range", "start_date": "2025-10-22", "end_date": "2025-10-25"}
              或 {"type": "search", "keyword": "成龙"}

    Returns:
        查询结果的文本描述
    """
    try:
        data = json.loads(input_str)
        query_type = data.get("type", "today")

        if query_type == "today":
            todos = todo_manager.get_today_todos()
            date = datetime.now().strftime("%Y-%m-%d")
            if todos:
                result = f"📅 今天（{date}）的待办:\n\n"
                result += todo_manager.format_todos_display(todos)
            else:
                result = f"📭 今天（{date}）没有待办事项"
            return result

        elif query_type == "date":
            date = data.get("date", "")
            if not date:
                return "❌ 错误：查询特定日期需要提供 date 参数"
            todos = todo_manager.get_todos(date)
            if todos:
                result = f"📅 {date} 的待办:\n\n"
                result += todo_manager.format_todos_display(todos)
            else:
                result = f"📭 {date} 没有待办事项"
            return result

        elif query_type == "range":
            start_date = data.get("start_date", "")
            end_date = data.get("end_date", "")
            if not start_date or not end_date:
                return "❌ 错误：查询日期范围需要提供 start_date 和 end_date"

            todos_by_date = todo_manager.get_todos_by_range(start_date, end_date)
            if todos_by_date:
                result = f"📅 {start_date} 到 {end_date} 的待办:\n\n"
                for date, todos in sorted(todos_by_date.items()):
                    result += f"\n📆 {date}\n"
                    result += todo_manager.format_todos_display(todos) + "\n"
            else:
                result = f"📭 {start_date} 到 {end_date} 没有待办事项"
            return result

        elif query_type == "search":
            keyword = data.get("keyword", "")
            if not keyword:
                return "❌ 错误：搜索需要提供 keyword 参数"

            results = todo_manager.search_todos(keyword)
            if results:
                result = f"🔍 搜索「{keyword}」的结果:\n\n"
                for date, todos in sorted(results.items()):
                    result += f"\n📆 {date}\n"
                    result += todo_manager.format_todos_display(todos) + "\n"
            else:
                result = f"📭 没有找到包含「{keyword}」的待办事项"
            return result

        else:
            return f"❌ 不支持的查询类型: {query_type}"

    except json.JSONDecodeError as e:
        return f"❌ JSON解析失败: {str(e)}"
    except Exception as e:
        return f"❌ 查询待办时发生错误: {str(e)}"


# 创建 LangChain Tool 实例
add_todo_tool = Tool(
    name="add_todo",
    description="""添加待办事项。当用户想要记录、添加、设置一个待办或提醒时使用此工具。

输入格式（JSON字符串）:
{
    "date": "YYYY-MM-DD格式的日期（必填）",
    "time": "HH:MM格式的时间（可选）",
    "content": "待办内容描述（必填）"
}

示例:
- 用户说"今天18点给成龙打电话" -> {"date": "2025-10-22", "time": "18:00", "content": "给成龙打电话"}
- 用户说"明天开会" -> {"date": "2025-10-23", "time": "", "content": "开会"}

注意：你需要自己将相对日期（今天、明天、后天等）转换为具体的YYYY-MM-DD格式。今天是 """ + datetime.now().strftime("%Y-%m-%d"),
    func=add_todo_tool_func
)

query_todo_tool = Tool(
    name="query_todo",
    description="""查询待办事项。当用户想要查看、询问待办事项时使用此工具。

输入格式（JSON字符串）:
1. 查询今天: {"type": "today"}
2. 查询特定日期: {"type": "date", "date": "YYYY-MM-DD"}
3. 查询日期范围: {"type": "range", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}
4. 关键词搜索: {"type": "search", "keyword": "关键词"}

示例:
- "今天有什么要做的" -> {"type": "today"}
- "明天的待办" -> {"type": "date", "date": "2025-10-23"}
- "搜索成龙相关的待办" -> {"type": "search", "keyword": "成龙"}
""",
    func=query_todo_tool_func
)


# 导出工具列表
todo_tools = [add_todo_tool, query_todo_tool]
