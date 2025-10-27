# 5. 好坏示例对比（引导）

- 类型: heading
- 来源: /Users/zhangyanhua/Desktop/AI/tushare/quantification/example/docs/GIT_COMMIT_DEEP_ANALYSIS.md

## 摘要
# Git Commit消息深度分析优化文档 ## 问题背景 ### 用户痛点 用户反馈："感觉还是不够清晰，现在生成的是 `chore: 清理项目文件和文档，删除环境变量` 但是我变更文件有51个之多呢" ### 根本原因 - **只读文件名列表**：LLM只看到文件名，没有实际代码变更内容 - **缺少diff分析**：没有深入分析每个文件的具体变更（新增/删除/修改了什么） - **Prompt不够详细**：没有明确要求LLM基于diff内容进行分析 - **diff长度限制太小**：之前只读取4000字符，无法涵盖51个文件的变更 ## 优化方案 ### 1. 文件分类统计（新增） **代码实现** (`git_commit_tools.py:49-84`): ```python # 解析 git status 输出，分类文件 status_lines = analysis['st
