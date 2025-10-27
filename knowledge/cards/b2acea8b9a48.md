# auto_commit_tool_func

- 类型: function
- 来源: /Users/zhangyanhua/Desktop/AI/tushare/quantification/example/src/tools/auto_commit_tools.py

## 摘要
自动执行完整的 Git 提交流程

工作流:
1. git add . (暂存所有变更)
2. 分析 git diff 生成 commit 消息
3. git commit -m "消息"

Args:
    user_request: 用户的额外说明（可选）
    
Returns:
    完整流程的执行结果
