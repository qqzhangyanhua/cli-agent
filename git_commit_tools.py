"""
Git Commit 工具 - LangChain Tool 封装
将 Git commit 消息生成功能封装为 LangChain 工具
"""

from langchain_core.tools import Tool
from git_tools import git_tools
from agent_llm import llm_code
from agent_config import LLM_CONFIG2
from langchain_core.messages import HumanMessage


def generate_commit_message_tool_func(input_str: str = "") -> str:
    """
    生成 Git commit 消息

    Args:
        input_str: 可选的额外说明（通常不需要）

    Returns:
        格式化的 commit 消息和使用说明
    """
    try:
        print(f"[Git分析] 分析代码变更...")

        # 分析 Git 变更
        analysis = git_tools.analyze_changes()

        if not analysis["success"]:
            error_msg = analysis.get('error', 'Git分析失败')
            print(f"[Git分析] ❌ {error_msg}")
            return f"❌ {error_msg}"

        print(f"[Git分析] ✅ 分析完成")
        print(f"[Git分析] {analysis['summary']}")
        print(f"[Git分析] 变更文件: {len(analysis['files_changed'])} 个")

        # 准备 diff 内容
        if analysis['has_staged']:
            diff_content = analysis['staged_diff']
            diff_type = "已暂存(staged)"
        elif analysis['has_unstaged']:
            diff_content = analysis['unstaged_diff']
            diff_type = "未暂存(unstaged)"
        else:
            diff_content = analysis['status']
            diff_type = "状态"

        # 获取 git status 的详细信息（包含文件状态标记）
        status_lines = analysis['status'].split('\n')

        # 分类统计文件变更
        deleted_files = []
        modified_files = []
        added_files = []

        for line in status_lines:
            if not line.strip():
                continue
            # Git status 格式: XY filename
            # D = deleted, M = modified, A = added, ?? = untracked
            if line.startswith(' D'):
                deleted_files.append(line[3:])
            elif line.startswith('D '):
                deleted_files.append(line[3:])
            elif line.startswith(' M'):
                modified_files.append(line[3:])
            elif line.startswith('M '):
                modified_files.append(line[3:])
            elif line.startswith('??'):
                added_files.append(line[3:])
            elif line.startswith('A '):
                added_files.append(line[3:])

        # 构建详细的文件变更统计
        file_stats = []
        if deleted_files:
            file_stats.append(f"删除 {len(deleted_files)} 个文件")
        if modified_files:
            file_stats.append(f"修改 {len(modified_files)} 个文件")
        if added_files:
            file_stats.append(f"新增 {len(added_files)} 个文件")

        file_stats_str = "、".join(file_stats) if file_stats else "未知变更"

        # 扩大 diff 长度限制，让 LLM 能看到更多细节
        max_diff_length = 8000
        if len(diff_content) > max_diff_length:
            diff_content = diff_content[:max_diff_length] + "\n\n... (diff太长，已截断)"

        # 获取最近的 commits 作为参考
        recent_commits_str = "\n".join(analysis.get('recent_commits', [])[:5])

        # 生成 commit 消息 - 增强版prompt
        prompt = f"""你是一个专业的Git commit消息生成器。你的任务是仔细阅读代码变更的diff，生成非常详细、精确的commit消息。

📊 **变更统计**:
- 总计: {len(analysis['files_changed'])} 个文件
- 详细: {file_stats_str}

📝 **删除的文件** ({len(deleted_files)}个):
{chr(10).join(['  - ' + f for f in deleted_files[:20]])}
{f"  ... 还有 {len(deleted_files) - 20} 个" if len(deleted_files) > 20 else ""}

✏️  **修改的文件** ({len(modified_files)}个):
{chr(10).join(['  - ' + f for f in modified_files[:20]])}
{f"  ... 还有 {len(modified_files) - 20} 个" if len(modified_files) > 20 else ""}

➕ **新增的文件** ({len(added_files)}个):
{chr(10).join(['  - ' + f for f in added_files[:20]])}
{f"  ... 还有 {len(added_files) - 20} 个" if len(added_files) > 20 else ""}

📄 **实际代码变更内容**({diff_type}):
```diff
{diff_content}
```

📜 **最近的commit记录**(参考风格):
{recent_commits_str if recent_commits_str else '(暂无历史commit)'}

🎯 **你的任务**:
1. **仔细阅读上面的diff内容**（不要只看文件名！）
2. **分析每个文件的实际变更**（新增了什么函数？删除了什么逻辑？修改了什么行为？）
3. **识别变更的核心意图**（这次提交要解决什么问题？实现什么功能？）
4. **生成非常详细、精确的commit消息**

📋 **分析框架（必须严格遵循）**:

**第1步：文件变更统计分析**
- 删除: {len(deleted_files)} 个文件 → 具体是什么类型？(文档/测试/代码/配置)
- 修改: {len(modified_files)} 个文件 → 修改了哪些核心模块？
- 新增: {len(added_files)} 个文件 → 新增了什么功能/模块？

**第2步：代码diff深度分析**（关键！）
仔细阅读上面的diff内容，回答：
- 新增的代码实现了什么功能？（看 +++ 行）
- 删除的代码移除了什么逻辑？（看 --- 行）
- 修改的代码改变了什么行为？（对比 - 和 + 行）
- 是否有函数/类的新增、删除、重命名？
- 是否有import语句变更？（说明依赖关系变化）
- 是否有注释/文档字符串更新？（说明意图）

**第3步：识别核心变更意图**
基于diff分析，这次提交的主要目的是：
- [ ] 新功能开发 (feat)
- [ ] Bug修复 (fix)
- [ ] 代码重构 (refactor)
- [ ] 文档更新 (docs)
- [ ] 性能优化 (perf)
- [ ] 测试相关 (test)
- [ ] 构建/工具/清理 (chore)

**第4步：生成commit消息**
格式要求:
- 遵循Conventional Commits规范
- 使用中文描述
- 格式: `<type>: <subject>`
- type从上面选择最合适的
- subject要**极其具体**地描述变更内容

**好的commit消息示例**（基于diff深度分析）:
✅ feat: 添加Todo管理工具并集成LangChain Tool接口
   → 说明了具体功能（Todo管理）+ 技术实现（LangChain Tool）

✅ refactor: 重构意图分析为LLM驱动的工具选择，移除硬编码规则
   → 说明了重构内容（意图分析）+ 新方案（LLM驱动）+ 删除内容（硬编码规则）

✅ feat: 实现流式LLM输出，优化问答响应体验
   → 说明了新功能（流式输出）+ 影响范围（问答）+ 效果（优化体验）

✅ chore: 删除28个markdown文档和测试文件，清理Python缓存
   → 精确数量（28个）+ 文件类型（markdown文档和测试文件）+ 清理内容（Python缓存）

✅ fix: 修复Git commit工具动态导入失败，改为静态导入
   → 问题定位（Git commit工具）+ 错误原因（动态导入失败）+ 解决方案（静态导入）

❌ **不好的示例**（没有分析diff）:
❌ chore: 清理项目文件 → 什么文件？几个？
❌ feat: 添加新功能 → 什么功能？
❌ refactor: 代码重构 → 重构了什么？怎么重构的？
❌ fix: 修复bug → 什么bug？怎么修的？

⚠️ **特别注意**:
- 不要只看文件名！必须看diff内容分析实际代码变更
- 如果删除了很多文档，必须说明具体数量和类型
- 如果修改了核心模块，必须说明修改了什么行为/逻辑
- 如果新增了功能，必须说明功能的具体作用

📤 **输出格式要求**:

**简单变更**（<5个文件 或 只有文档/配置变更）:
只返回一行commit消息：
```
<type>: <详细的subject描述>
```

**复杂变更**（≥10个文件 或 涉及多个模块）:
返回多行格式：
```
<type>: <简洁的subject总结>（50字内）

<空行>
<body部分 - 详细说明>:
- 第1个重要变更（基于diff分析）
- 第2个重要变更（基于diff分析）
- 第3个重要变更（基于diff分析）
- ...（3-5行，每行说明一个具体变更）
```

**示例输出**（复杂变更）:
```
feat: 实现Git commit消息深度分析生成

- 新增文件分类统计功能（deleted/modified/added）
- 扩大diff读取长度到8000字符，支持更详细分析
- 增强LLM prompt，要求基于diff内容而非文件名生成消息
- 添加4步分析框架（统计→diff→意图→生成）
- 提供好坏示例对比，优化生成质量
```

🚀 **现在开始分析**:
请仔细阅读上面的diff内容，按照4步框架进行深度分析，然后生成commit消息。

⚠️ 重要提醒：
1. **必须阅读diff的具体内容**，不能只看文件名列表
2. **必须分析代码层面的变更**（函数、类、逻辑、导入等）
3. **commit消息要反映diff的实际内容**，而不是猜测

只返回commit消息内容，不要输出分析过程:"""

        print(f"[Commit生成] 使用模型: {LLM_CONFIG2['model']}")

        # 调用 LLM 生成
        result = llm_code.invoke([HumanMessage(content=prompt)])
        commit_message = result.content.strip()

        # 清理可能的 markdown 格式
        if commit_message.startswith("```"):
            lines = commit_message.split('\n')
            commit_message = '\n'.join(lines[1:-1]) if len(lines) > 2 else commit_message

        print(f"[Commit生成] ✅ 生成完成")

        # 处理 commit 消息中的双引号，避免命令执行问题
        def escape_commit_message(msg: str) -> str:
            """转义 commit 消息中的双引号，确保命令可以正确执行"""
            # 将双引号替换为单引号，避免命令行解析问题
            return msg.replace('"', "'")
        
        escaped_commit_message = escape_commit_message(commit_message)
        
        # 格式化响应 - 直接显示可执行的命令
        response = "📝 Git Commit消息生成完成\n\n"
        
        response += f"📊 变更摘要:\n"
        response += f"  • 变更文件: {len(analysis['files_changed'])} 个\n"
        if analysis['files_changed']:
            response += f"  • 主要文件:\n"
            for f in analysis['files_changed'][:5]:
                response += f"    - {f}\n"
            if len(analysis['files_changed']) > 5:
                response += f"    ... 还有 {len(analysis['files_changed']) - 5} 个文件\n"

        response += f"\n💡 直接执行以下命令:\n"
        response += "─" * 60 + "\n"
        
        if analysis['has_staged']:
            response += f'git commit -m "{escaped_commit_message}"\n'
        else:
            response += f"git add .  # 先暂存变更\n"
            response += f'git commit -m "{escaped_commit_message}"\n'
        
        response += "─" * 60 + "\n"
        
        # 如果原始消息包含双引号，提供说明
        if '"' in commit_message:
            response += "\n💡 注意: 原消息中的双引号已转换为单引号，确保命令正确执行\n"

        return response

    except Exception as e:
        error_msg = f"❌ 生成commit消息失败: {str(e)}"
        print(f"[Commit生成] {error_msg}")
        return error_msg


# 创建 LangChain Tool 实例
generate_commit_tool = Tool(
    name="generate_commit",
    description="""生成Git commit消息。当用户想要生成、创建commit日志/消息时使用此工具。

适用场景:
- "生成commit日志"
- "生成commit消息"
- "帮我写commit message"
- "根据git diff生成提交信息"

此工具会:
1. 自动运行 git diff 分析代码变更
2. 根据变更内容生成符合规范的commit消息
3. 提供使用方法

不需要任何参数输入。""",
    func=generate_commit_message_tool_func
)


# 导出工具
git_commit_tools = [generate_commit_tool]
