"""
待办事项处理节点
处理待办事项的添加和查询
"""

import json
from datetime import datetime
from langchain_core.messages import HumanMessage

from src.core.agent_config import AgentState
from src.core.agent_llm import llm
from src.core.json_utils import extract_json_str, safe_json_loads
from src.tools.todo_manager import todo_manager


def todo_processor(state: AgentState) -> dict:
    """处理待办事项的添加和查询"""
    user_input = state["user_input"]
    intent = state["intent"]

    print(f"\n[待办处理] 处理待办事项...")
    print(f"           意图: {intent}")

    if intent == "add_todo":
        # 使用LLM解析待办信息
        prompt = f"""从用户输入中提取待办事项信息，返回JSON格式。

用户输入: {user_input}

需要提取:
1. date: 日期（格式：YYYY-MM-DD）。如果用户说\"今天\"，使用今天日期；\"明天\"使用明天日期；具体日期按实际解析
2. time: 时间（格式：HH:MM），如果没有明确时间，返回空字符串
3. content: 待办内容（简洁描述，去掉日期时间信息）

今天是: {datetime.now().strftime("%Y-%m-%d")}

示例:
输入: \"今天18点我要给陈龙打电话\"
输出: {{"date": "2024-01-22", "time": "18:00", "content": "给陈龙打电话"}}

输入: \"明天上午10点开会\"
输出: {{"date": "2024-01-23", "time": "10:00", "content": "开会"}}

输入: \"提醒我周五下午3点半交报告\"
输出: {{"date": "2024-01-26", "time": "15:30", "content": "交报告"}}

只返回JSON，不要其他内容:"""

        result = llm.invoke([HumanMessage(content=prompt)])
        response_text = result.content.strip()

        # 提取并解析 JSON（健壮）
        try:
            response_text = extract_json_str(response_text)
            parsed_obj, err = safe_json_loads(response_text)
            if err:
                raise json.JSONDecodeError(err, response_text, 0)
            parsed = parsed_obj
            date = parsed.get("date", "")
            time = parsed.get("time", "")
            content = parsed.get("content", "")

            print(f"[待办处理] 解析结果 - 日期:{date} 时间:{time} 内容:{content}")

            # 验证日期格式
            if date:
                try:
                    datetime.strptime(date, "%Y-%m-%d")
                except ValueError:
                    print(f"[待办处理] ❌ 日期格式无效: {date}")
                    return {
                        "response": f"❌ 日期格式无效: {date}\n\n请使用正确的日期格式，例如：「今天18点给陈龙打电话」",
                        "error": "Invalid date format",
                    }

            # 验证时间格式（如果提供了时间）
            if time:
                try:
                    datetime.strptime(time, "%H:%M")
                except ValueError:
                    print(f"[待办处理] ⚠️  时间格式异常: {time}，将忽略时间")
                    time = ""

            if date and content:
                # 添加待办
                todo_item = todo_manager.add_todo(date, time, content)

                if todo_item:
                    response = f"✅ 待办已添加！\n\n"
                    response += f"📅 日期: {date}\n"
                    if time:
                        response += f"⏰ 时间: {time}\n"
                    response += f"📝 内容: {content}\n"
                    response += f"\n💡 你可以随时问我「今天有什么要做的？」或「{date}有什么待办？」来查看待办事项。"
                else:
                    response = "❌ 添加待办失败，请重试。"
            else:
                response = "❌ 无法解析待办信息，请提供更明确的日期和内容。\n\n示例：「今天18点给陈龙打电话」"

            return {
                "response": response,
                "todo_action": "add",
                "todo_date": date,
                "todo_time": time,
                "todo_content": content,
            }

        except json.JSONDecodeError as e:
            print(f"[待办处理] JSON解析失败: {e}")
            return {
                "response": "❌ 解析待办信息失败，请重试。\n\n示例：「今天18点给陈龙打电话」",
                "error": str(e),
            }

    elif intent == "query_todo":
        # 使用LLM解析查询意图
        prompt = f"""从用户输入中提取查询信息，返回JSON格式。

用户输入: {user_input}

需要提取:
1. query_type: 查询类型
   - \"today\": 查询今天
   - \"date\": 查询特定日期
   - \"range\": 查询日期范围
   - \"upcoming\": 查询未来几天
   - \"search\": 搜索关键词
2. date: 日期（YYYY-MM-DD），适用于 date 类型
3. start_date: 开始日期，适用于 range 类型
4. end_date: 结束日期，适用于 range 类型
5. days: 天数，适用于 upcoming 类型
6. keyword: 搜索关键词，适用于 search 类型

今天是: {datetime.now().strftime("%Y-%m-%d")}

示例:
\"今天有什么要做的？\" -> {{\"query_type\": \"today\"}}
\"明天有什么待办？\" -> {{\"query_type\": \"date\", \"date\": \"2024-01-23\"}}
\"这周有什么任务？\" -> {{\"query_type\": \"range\", \"start_date\": \"2024-01-22\", \"end_date\": \"2024-01-28\"}}
\"未来3天的待办\" -> {{\"query_type\": \"upcoming\", \"days\": 3}}
\"陈龙相关的待办\" -> {{\"query_type\": \"search\", \"keyword\": \"陈龙\"}}

只返回JSON:"""

        result = llm.invoke([HumanMessage(content=prompt)])
        response_text = result.content.strip()

        # 提取JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        try:
            parsed = json.loads(response_text)
            query_type = parsed.get("query_type", "today")

            print(f"[待办处理] 查询类型: {query_type}")

            response = ""

            if query_type == "today":
                todos = todo_manager.get_today_todos()
                date = datetime.now().strftime("%Y-%m-%d")
                response = f"📅 今天（{date}）的待办:\n\n"
                if todos:
                    response += todo_manager.format_todos_display(todos)
                else:
                    response += "📭 今天没有待办事项"

            elif query_type == "date":
                date = parsed.get("date", "")
                if date:
                    todos = todo_manager.get_todos(date)
                    response = f"📅 {date} 的待办:\n\n"
                    if todos:
                        response += todo_manager.format_todos_display(todos)
                    else:
                        response += "📭 这天没有待办事项"
                else:
                    response = "❌ 无法解析日期"

            elif query_type == "range":
                start_date = parsed.get("start_date", "")
                end_date = parsed.get("end_date", "")
                if start_date and end_date:
                    todos_by_date = todo_manager.get_todos_by_range(
                        start_date, end_date
                    )
                    response = f"📅 {start_date} 到 {end_date} 的待办:\n\n"
                    if todos_by_date:
                        for date, todos in sorted(todos_by_date.items()):
                            response += f"\n📆 {date}\n"
                            response += todo_manager.format_todos_display(todos) + "\n"
                    else:
                        response += "📭 这个时间段没有待办事项"
                else:
                    response = "❌ 无法解析日期范围"

            elif query_type == "upcoming":
                days = parsed.get("days", 7)
                todos_by_date = todo_manager.get_upcoming_todos(days)
                response = f"📅 未来 {days} 天的待办:\n\n"
                if todos_by_date:
                    for date, todos in sorted(todos_by_date.items()):
                        response += f"\n📆 {date}\n"
                        response += todo_manager.format_todos_display(todos) + "\n"
                else:
                    response += "📭 未来几天没有待办事项"

            elif query_type == "search":
                keyword = parsed.get("keyword", "")
                if keyword:
                    results = todo_manager.search_todos(keyword)
                    response = f"🔍 搜索「{keyword}」的结果:\n\n"
                    if results:
                        for date, todos in sorted(results.items()):
                            response += f"\n📆 {date}\n"
                            response += todo_manager.format_todos_display(todos) + "\n"
                    else:
                        response += f"📭 没有找到包含「{keyword}」的待办事项"
                else:
                    response = "❌ 请提供搜索关键词"

            return {
                "response": response,
                "todo_action": "query",
                "todo_result": response,
            }

        except json.JSONDecodeError as e:
            print(f"[待办处理] JSON解析失败: {e}")
            return {
                "response": "❌ 解析查询失败，请重试。\n\n示例：「今天有什么要做的？」",
                "error": str(e),
            }

    else:
        return {"response": "❌ 未知的待办操作", "error": "Unknown todo intent"}
