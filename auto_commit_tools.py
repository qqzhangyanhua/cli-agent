"""
Git 自动提交工具 - 完整的 Git 工作流
实现：
- auto_commit: git add -> 生成commit消息 -> git commit
- full_git_workflow: git pull -> git add -> 生成commit消息 -> git commit -> git push
"""

import subprocess
from typing import Dict, Optional
from langchain_core.tools import Tool
from git_tools import git_tools
from git_commit_tools import generate_commit_message_tool_func
from agent_utils import execute_terminal_command


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
    
    # 限制 diff 长度
    max_diff_length = 8000
    if len(diff_content) > max_diff_length:
        diff_content = diff_content[:max_diff_length] + "\n\n... (diff太长，已截断)"
    
    # 获取最近的 commits 作为参考
    recent_commits_str = "\n".join(analysis.get('recent_commits', [])[:5])
    
    # 生成 commit 消息的 prompt（使用与 git_commit_tools.py 相同的逻辑）
    from agent_llm import llm_code
    from langchain_core.messages import HumanMessage
    
    prompt = f"""你是一个专业的Git commit消息生成器。基于下面的代码变更，生成简洁、精确的commit消息。

📊 变更统计:
- 总计: {len(analysis['files_changed'])} 个文件 ({file_stats_str})

📄 代码变更内容:
```diff
{diff_content}
```

📜 最近的commit记录(参考风格):
{recent_commits_str if recent_commits_str else '(暂无历史commit)'}

🎯 要求:
1. 遵循 Conventional Commits 规范
2. 使用中文描述
3. 格式: <type>: <subject>
4. type选择: feat/fix/refactor/docs/perf/test/chore
5. subject要具体描述变更内容

只返回一行commit消息，不要其他内容。"""
    
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

