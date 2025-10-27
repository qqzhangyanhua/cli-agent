# query_todo_tool_func

- 类型: function
- 来源: /Users/zhangyanhua/Desktop/AI/tushare/quantification/example/src/tools/todo_tools.py

## 摘要
查询待办事项

Args:
    input_str: JSON格式的查询条件
    例如: {"type": "today"} 或 {"type": "date", "date": "2025-10-22"}
          或 {"type": "range", "start_date": "2025-10-22", "end_date": "2025-10-25"}
          或 {"type": "search", "keyword": "成龙"}

Returns:
    查询结果的文本描述
