# get_git_diff

- 类型: function
- 来源: /Users/zhangyanhua/Desktop/AI/tushare/quantification/example/src/tools/git_tools.py

## 摘要
获取Git diff

Args:
    staged: 是否获取已暂存的diff（默认False，获取工作区diff）

Returns:
    {
        "success": bool,
        "diff": str,
        "has_diff": bool,
        "files_changed": list,
        "error": str
    }
