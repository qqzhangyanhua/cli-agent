"""
Git 自动提交工具 - 完整的 Git 工作流
实现：
- auto_commit: git add -> 生成commit消息 -> git commit
- full_git_workflow: git pull -> git add -> 生成commit消息 -> git commit -> git push
"""

import subprocess
from typing import Dict, Optional
from langchain_core.tools import Tool
from src.tools.git_tools import git_tools
from src.tools.git_commit_tools import generate_commit_message_tool_func
from src.core.agent_utils import execute_terminal_command


def git_add_all() -> Dict:
    """
    执行 git add . 暂存所有变更
    
    Returns:
        {
            "success": bool,
            "message": str,
            "error": str
        }
    """
    print(f"[Git Add] 暂存所有变更...")
    
    # 检查是否是 Git 仓库
    if not git_tools.check_git_repo():
        return {
            "success": False,
            "error": "❌ 当前目录不是 Git 仓库",
            "message": ""
        }
    
    # 检查是否有变更
    status = git_tools.get_git_status()
    if not status.get("has_changes", False):
        return {
            "success": False,
            "error": "⚠️ 工作区没有变更，无需执行 git add",
            "message": ""
        }
    
    try:
        # 执行 git add .
        result = subprocess.run(
            ["git", "add", "."],
            cwd=".",
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=10,
        )
        
        if result.returncode == 0:
            # 获取暂存后的状态
            staged_diff = git_tools.get_git_diff(staged=True)
            files_count = len(staged_diff.get("files_changed", []))
            
            message = f"✅ 已暂存 {files_count} 个文件的变更"
            print(f"[Git Add] {message}")
            
            return {
                "success": True,
                "message": message,
                "files_count": files_count,
                "error": ""
            }
        else:
            error = result.stderr.strip() if result.stderr else "未知错误"
            return {
                "success": False,
                "error": f"❌ git add 失败: {error}",
                "message": ""
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"❌ 执行 git add 时发生错误: {str(e)}",
            "message": ""
        }


def git_commit_with_message(message: str) -> Dict:
    """
    执行 git commit -m "message"
    
    Args:
        message: commit 消息
        
    Returns:
        {
            "success": bool,
            "message": str,
            "commit_hash": str,
            "error": str
        }
    """
    if not message or not message.strip():
        return {
            "success": False,
            "error": "❌ commit 消息不能为空",
            "message": "",
            "commit_hash": ""
        }
    
    print(f"[Git Commit] 提交变更...")
    
    try:
        # 执行 git commit
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=".",
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=10,
        )
        
        if result.returncode == 0:
            # 提取 commit hash
            commit_hash = ""
            output = result.stdout.strip()
            
            # 尝试从输出中提取 commit hash
            # 输出格式通常是: [branch commit_hash] message
            if "[" in output and "]" in output:
                parts = output.split("]")[0].split()
                if len(parts) >= 2:
                    commit_hash = parts[-1]
            
            success_msg = f"✅ 代码已提交"
            if commit_hash:
                success_msg += f" (commit: {commit_hash[:7]})"
            
            print(f"[Git Commit] {success_msg}")
            
            return {
                "success": True,
                "message": success_msg,
                "commit_hash": commit_hash,
                "error": ""
            }
        else:
            error = result.stderr.strip() if result.stderr else result.stdout.strip()
            return {
                "success": False,
                "error": f"❌ git commit 失败: {error}",
                "message": "",
                "commit_hash": ""
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"❌ 执行 git commit 时发生错误: {str(e)}",
            "message": "",
            "commit_hash": ""
        }


def auto_commit_tool_func(user_request: str = "") -> str:
    """
    自动执行完整的 Git 提交流程
    
    工作流:
    1. git add . (暂存所有变更)
    2. 分析 git diff 生成 commit 消息
    3. git commit -m "消息"
    
    Args:
        user_request: 用户的额外说明（可选）
        
    Returns:
        完整流程的执行结果
    """
    print(f"\n{'='*60}")
    print(f"🚀 启动 Git 自动提交工作流")
    print(f"{'='*60}\n")
    
    response = ""
    
    # 第一步：git add .
    print(f"📦 步骤 1/3: 暂存变更")
    add_result = git_add_all()
    
    if not add_result["success"]:
        return f"""❌ Git 提交流程失败

{add_result['error']}

请检查后重试。"""
    
    response += f"{add_result['message']}\n"
    files_count = add_result.get("files_count", 0)
    
    # 第二步：生成 commit 消息
    print(f"\n💡 步骤 2/3: 生成 commit 消息")
    
    # 获取当前分支信息
    branch_info = git_tools.get_current_branch()
    current_branch = branch_info.get("branch", "unknown") if branch_info.get("success") else "unknown"
    print(f"[Git Commit] 当前分支: {current_branch}")
    
    # 分析变更并生成消息
    analysis = git_tools.analyze_changes()
    
    if not analysis["success"]:
        return f"""❌ Git 提交流程失败

步骤 1: ✅ 已暂存 {files_count} 个文件
步骤 2: ❌ {analysis.get('error', '生成 commit 消息失败')}

请检查后重试。"""
    
    # 准备 diff 内容
    if analysis['has_staged']:
        diff_content = analysis['staged_diff']
    else:
        return f"""❌ Git 提交流程失败

步骤 1: ✅ 已暂存 {files_count} 个文件
步骤 2: ❌ 没有已暂存的变更，无法生成 commit 消息

请检查后重试。"""
    
    # 获取文件状态
    status_lines = analysis['status'].split('\n')
    
    # 分类统计文件变更
    deleted_files = []
    modified_files = []
    added_files = []
    
    for line in status_lines:
        if not line.strip():
            continue
        if line.startswith(' D') or line.startswith('D '):
            deleted_files.append(line[3:])
        elif line.startswith(' M') or line.startswith('M '):
            modified_files.append(line[3:])
        elif line.startswith('??') or line.startswith('A '):
            added_files.append(line[3:])
    
    file_stats = []
    if deleted_files:
        file_stats.append(f"删除 {len(deleted_files)} 个")
    if modified_files:
        file_stats.append(f"修改 {len(modified_files)} 个")
    if added_files:
        file_stats.append(f"新增 {len(added_files)} 个")
    
    file_stats_str = "、".join(file_stats) if file_stats else "未知变更"
    
    # 获取最近的 commits 作为参考
    recent_commits_str = "\n".join(analysis.get('recent_commits', [])[:5])
    
    # 使用与 git_commit_tools.py 相同的详细生成逻辑
    from src.core.agent_llm import llm_code
    from langchain_core.messages import HumanMessage
    
    # 扩大 diff 长度限制，让 LLM 能看到更多细节
    max_diff_length = 8000
    if len(diff_content) > max_diff_length:
        diff_content = diff_content[:max_diff_length] + "\n\n... (diff太长，已截断)"
    
    # 生成 commit 消息 - 使用详细版prompt（与git_commit_tools.py保持一致）
    prompt = f"""你是一个专业的Git commit消息生成器。你的任务是仔细阅读代码变更的diff，生成非常详细、精确的commit消息。

🌿 **分支信息**:
- 当前分支: {current_branch}

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

📄 **实际代码变更内容**:
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
- Title格式: `<type>: <subject>`
- Description格式: `【<branch>分支】\n<详细描述>`
- branch是当前分支名称
- type从上面选择最合适的
- subject要**极其具体**地描述变更内容
- 分支信息放在description的第一行

**好的commit消息示例**（基于diff深度分析）:

✅ 示例1（简单变更）:
Title: feat: 添加Todo管理工具并集成LangChain Tool接口
Description: 【feature/todo-tools分支】
说明了具体功能（Todo管理）+ 技术实现（LangChain Tool）

✅ 示例2（复杂变更）:
Title: refactor: 重构意图分析为LLM驱动的工具选择
Description: 【refactor/intent-analysis分支】
- 移除硬编码的意图识别规则
- 集成LangChain工具选择机制  
- 优化工具调用的准确性和灵活性

✅ 示例3（主分支）:
Title: feat: 实现流式LLM输出，优化问答响应体验
Description: 【main分支】
说明了新功能（流式输出）+ 影响范围（问答）+ 效果（优化体验）

✅ 示例4（清理操作）:
Title: chore: 删除28个markdown文档和测试文件，清理Python缓存
Description: 【cleanup/docs分支】
- 删除过时的文档文件
- 移除无用的测试文件
- 清理Python缓存目录

⚠️ **特别注意**:
- 不要只看文件名！必须看diff内容分析实际代码变更
- 如果删除了很多文档，必须说明具体数量和类型
- 如果修改了核心模块，必须说明修改了什么行为/逻辑
- 如果新增了功能，必须说明功能的具体作用
- **分支信息处理**：
  • Title不包含分支信息，只有 <type>: <subject>
  • Description第一行必须是：【{current_branch}分支】
  • 分支信息放在description开头，用【】包围

📤 **输出格式要求**:

**简单变更**（<5个文件 或 只有文档/配置变更）:
返回两行格式：
```
<type>: <详细的subject描述>

【{current_branch}分支】
```

**复杂变更**（≥10个文件 或 涉及多个模块）:
返回多行格式：
```
<type>: <简洁的subject总结>

【{current_branch}分支】
- 第1个重要变更（基于diff分析）
- 第2个重要变更（基于diff分析）
- 第3个重要变更（基于diff分析）
- ...（3-5行，每行说明一个具体变更）
```

🚀 **现在开始分析**:
请仔细阅读上面的diff内容，按照4步框架进行深度分析，然后生成commit消息。

⚠️ 重要提醒：
1. **必须阅读diff的具体内容**，不能只看文件名列表
2. **必须分析代码层面的变更**（函数、类、逻辑、导入等）
3. **commit消息要反映diff的实际内容**，而不是猜测
4. **必须按照新格式生成commit消息**：
   - Title: <type>: <subject>（不包含分支信息）
   - Description: 【{current_branch}分支】开头，然后是详细描述
   - 中间用空行分隔

只返回commit消息内容，不要输出分析过程:"""
    
    try:
        result = llm_code.invoke([HumanMessage(content=prompt)])
        commit_message = result.content.strip()
        
        # 清理可能的 markdown 格式
        if commit_message.startswith("```"):
            lines = commit_message.split('\n')
            commit_message = '\n'.join(lines[1:-1]) if len(lines) > 2 else commit_message
        
        # 转义双引号
        commit_message = commit_message.replace('"', "'")
        
        print(f"[Git Commit] 生成的消息:")
        print(f"  {commit_message}")
        
    except Exception as e:
        return f"""❌ Git 提交流程失败

步骤 1: ✅ 已暂存 {files_count} 个文件
步骤 2: ❌ 生成 commit 消息失败: {str(e)}

请检查后重试。"""
    
    response += f"💬 生成的 commit 消息:\n  {commit_message}\n"
    
    # 第三步：执行 git commit
    print(f"\n✍️  步骤 3/3: 提交代码")
    commit_result = git_commit_with_message(commit_message)
    
    if not commit_result["success"]:
        return f"""❌ Git 提交流程失败

步骤 1: ✅ 已暂存 {files_count} 个文件
步骤 2: ✅ 已生成 commit 消息
步骤 3: ❌ {commit_result['error']}

你可以手动执行:
  git commit -m "{commit_message}"
"""
    
    response += f"{commit_result['message']}\n"
    
    # 成功完成
    print(f"\n{'='*60}")
    print(f"✅ Git 自动提交完成！")
    print(f"{'='*60}\n")
    
    final_response = f"""
🎉 Git 自动提交流程完成！

{'─'*60}
📦 步骤 1: ✅ 已暂存 {files_count} 个文件 ({file_stats_str})

💡 步骤 2: ✅ 生成 commit 消息
  {commit_message}

✍️  步骤 3: ✅ 代码已提交 {f'(commit: {commit_result["commit_hash"][:7]})' if commit_result.get("commit_hash") else ''}
{'─'*60}

💡 提示: 使用 'git log' 查看提交历史
"""
    
    return final_response


# 创建 LangChain Tool
auto_commit_tool = Tool(
    name="auto_commit",
    description="""自动执行完整的 Git 提交流程。

适用场景:
- "提交代码"
- "自动提交"
- "生成并提交commit"
- "一键提交"
- "commit并提交"

此工具会自动执行:
1. git add . (暂存所有变更)
2. 分析代码变更并生成commit消息
3. git commit -m "消息" (执行提交)

不需要任何参数，会自动完成整个流程。
""",
    func=auto_commit_tool_func
)


def git_pull_tool_func(user_request: str = "") -> str:
    """
    执行 git pull 拉取最新代码
    
    Returns:
        执行结果
    """
    print(f"\n{'='*60}")
    print(f"⬇️  执行 Git Pull")
    print(f"{'='*60}\n")
    
    result = git_tools.git_pull()
    
    if result["success"]:
        response = f"""
✅ Git Pull 完成！

{result['message']}
"""
        if result.get("has_updates"):
            response += "\n📥 已更新到最新版本"
        
        return response
    else:
        return f"""
❌ Git Pull 失败

{result['error']}

💡 请检查：
  • 是否有网络连接
  • 是否有未解决的冲突
  • 可以手动执行: git pull
"""


def git_push_tool_func(user_request: str = "") -> str:
    """
    执行 git push 推送代码到远程仓库
    
    Returns:
        执行结果
    """
    print(f"\n{'='*60}")
    print(f"⬆️  执行 Git Push")
    print(f"{'='*60}\n")
    
    # 获取当前分支
    branch_info = git_tools.get_current_branch()
    
    if not branch_info["success"]:
        return f"""
❌ Git Push 失败

{branch_info['error']}
"""
    
    branch = branch_info["branch"]
    print(f"[Git Push] 当前分支: {branch}")
    
    # 执行 push
    result = git_tools.git_push(branch)
    
    if result["success"]:
        return f"""
✅ Git Push 完成！

{result['message']}

💡 代码已推送到远程仓库
"""
    else:
        return f"""
❌ Git Push 失败

{result['error']}

💡 请检查：
  • 是否有网络连接
  • 是否有推送权限
  • 可以手动执行: git push origin {branch}
"""


# 创建 LangChain Tool
git_pull_tool = Tool(
    name="git_pull",
    description="""执行 git pull 拉取最新代码。

适用场景:
- "拉取代码"
- "git pull"
- "更新代码"
- "同步远程代码"

不需要任何参数。
""",
    func=git_pull_tool_func
)


git_push_tool = Tool(
    name="git_push",
    description="""执行 git push 推送代码到远程仓库。

适用场景:
- "推送代码"
- "git push"
- "上传代码"
- "推送到远程"

自动识别当前分支并推送到对应的远程分支（origin/<branch>）。
不需要任何参数。
""",
    func=git_push_tool_func
)


# 导出工具
auto_commit_tools = [auto_commit_tool, git_pull_tool, git_push_tool]


# ============================================
# 测试代码
# ============================================

if __name__ == "__main__":
    print("🧪 测试 Git 自动提交工具")
    print("="*80)
    
    # 测试完整流程
    result = auto_commit_tool_func("")
    print(result)

