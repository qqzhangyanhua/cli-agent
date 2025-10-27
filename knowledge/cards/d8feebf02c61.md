# analyze_changes

- 类型: function
- 来源: /Users/zhangyanhua/Desktop/AI/tushare/quantification/example/src/tools/git_tools.py

## 摘要
分析当前的变更，返回详细信息供LLM生成commit消息

Returns:
    {
        "success": bool,
        "status": str,
        "unstaged_diff": str,
        "staged_diff": str,
        "files_changed": list,
        "recent_commits": list,
        "summary": str,
        "error": str
    }
