# simple_tool_calling_node

- 类型: function
- 来源: /Users/zhangyanhua/Desktop/AI/tushare/quantification/example/src/mcp/agent_tool_calling.py

## 摘要
简化版工具调用节点 - 动态工具列表，零硬编码
使用 LLM 选择工具，然后自动分发调用

Args:
    state: 当前状态（字典格式）
    enable_streaming: 是否启用流式输出（问答时使用）
