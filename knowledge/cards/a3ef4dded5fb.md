# build_agent

- 类型: function
- 来源: /Users/zhangyanhua/Desktop/AI/tushare/quantification/example/src/core/agent_workflow.py

## 摘要
构建AI智能体工作流 - 充分利用 LangChain 工具调用特性

核心改进：
1. 使用 LangChain Tool Calling 替代硬编码意图分析
2. LLM 自主选择工具并调用
3. 简化工作流，减少不必要的节点
