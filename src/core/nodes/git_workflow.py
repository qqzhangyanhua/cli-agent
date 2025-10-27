"""
Git 工作流节点
包含 commit 消息生成、add、commit、pull、push 等节点
"""

import re
import time
from src.core.agent_config import AgentState
from src.tools.git_tools import git_tools
from src.tools.auto_commit_tools import git_add_all, git_commit_with_message
from src.tools.git_commit_tools import generate_commit_message_tool_func
from src.core.logger import get_logger, log_json_event

_log = get_logger("nodes")


def git_commit_generator(state: AgentState) -> dict:
    """生成Git commit消息"""
    print(f"[Git Commit] 调用Git commit工具...")
    try:
        response = generate_commit_message_tool_func()
        print(f"[Git Commit] ✅ 生成完成")
        return {"response": response}
    except Exception as e:
        error_msg = f"❌ Git commit消息生成失败: {str(e)}"
        print(f"[Git Commit] {error_msg}")
        return {"response": error_msg, "error": str(e)}


def git_add_node(state: AgentState) -> dict:
    """Git 工作流节点 1: 执行 git add ."""
    print(f"\n📦 [Git 工作流 1/3] 暂存变更...")
    try:
        result = git_add_all()
        if result["success"]:
            files_count = result.get("files_count", 0)
            print(f"[Git Add] ✅ {result['message']}")
            return {"git_add_success": True, "git_files_count": files_count, "response": result["message"]}
        else:
            error_msg = result.get("error", "git add 失败")
            print(f"[Git Add] ❌ {error_msg}")
            return {"git_add_success": False, "response": f"❌ Git 提交流程终止\n\n{error_msg}", "error": error_msg}
    except Exception as e:
        print(f"[Git Add] ❌ 异常: {e}")
        return {"git_add_success": False, "response": f"❌ Git add 执行失败: {str(e)}", "error": str(e)}


def git_commit_message_generator_node(state: AgentState) -> dict:
    """Git 工作流节点 2: 生成 commit 消息"""
    print(f"\n💡 [Git 工作流 2/3] 生成 commit 消息...")
    try:
        result_text = generate_commit_message_tool_func("")
        if "❌" in result_text:
            print(f"[Commit 生成] ❌ 生成失败")
            return {"git_commit_message_generated": False, "response": f"❌ Git 提交流程终止\n\n步骤 1: ✅ 已暂存变更\n步骤 2: ❌ {result_text}", "error": result_text}
        
        commit_message = ""
        if 'git commit -m "' in result_text:
            match = re.search(r'git commit -m "([^"]+)"', result_text)
            if match:
                commit_message = match.group(1)
        
        if not commit_message:
            return {"git_commit_message_generated": False, "response": "❌ 无法提取 commit 消息", "error": "parse_error"}
        
        print(f"[Commit 生成] ✅ 生成完成")
        return {"git_commit_message_generated": True, "git_commit_message": commit_message, "git_file_stats": "变更", "response": f"✅ 已生成 commit 消息:\n  {commit_message}"}
    except Exception as e:
        print(f"[Commit 生成] ❌ 异常: {e}")
        return {"git_commit_message_generated": False, "response": f"❌ 生成失败: {str(e)}", "error": str(e)}


def git_commit_executor_node(state: AgentState) -> dict:
    """Git 工作流节点 3: 执行 git commit"""
    print(f"\n✍️  [Git 工作流 3/3] 提交代码...")
    commit_message = state.get("git_commit_message", "")
    if not commit_message:
        return {"response": "❌ 缺少 commit 消息", "error": "no_message"}
    
    try:
        result = git_commit_with_message(commit_message)
        if result["success"]:
            commit_hash = result.get("commit_hash", "")
            print(f"[Git Commit] ✅ {result['message']}")
            return {"response": f"🎉 Git 自动提交流程完成!\n\n✅ 代码已提交 (commit: {commit_hash[:7] if commit_hash else ''})", "git_commit_success": True, "git_commit_hash": commit_hash}
        else:
            error_msg = result.get("error", "git commit 失败")
            print(f"[Git Commit] ❌ {error_msg}")
            return {"response": f"❌ Git 提交失败: {error_msg}", "git_commit_success": False, "error": error_msg}
    except Exception as e:
        print(f"[Git Commit] ❌ 异常: {e}")
        return {"response": f"❌ 执行失败: {str(e)}", "git_commit_success": False, "error": str(e)}


def git_pull_node(state: AgentState) -> dict:
    """Git 工作流节点: 执行 git pull"""
    print(f"\n⬇️  [Git Pull] 拉取最新代码...")
    try:
        result = git_tools.git_pull()
        if result["success"]:
            has_updates = result.get("has_updates", False)
            print(f"[Git Pull] {result['message']}")
            return {"git_pull_success": True, "git_pull_has_updates": has_updates, "response": result["message"]}
        else:
            error_msg = result.get("error", "git pull 失败")
            print(f"[Git Pull] ❌ {error_msg}")
            return {"git_pull_success": False, "response": f"❌ Git pull 失败: {error_msg}", "error": error_msg}
    except Exception as e:
        print(f"[Git Pull] ❌ 异常: {e}")
        return {"git_pull_success": False, "response": f"❌ Git pull 执行失败: {str(e)}", "error": str(e)}


def git_push_node(state: AgentState) -> dict:
    """Git 工作流节点: 执行 git push"""
    print(f"\n⬆️  [Git Push] 推送代码到远程...")
    try:
        branch_info = git_tools.get_current_branch()
        if not branch_info["success"]:
            return {"git_push_success": False, "response": "❌ 无法获取当前分支", "error": branch_info.get("error")}
        
        branch = branch_info["branch"]
        result = git_tools.git_push(branch)
        if result["success"]:
            print(f"[Git Push] ✅ {result['message']}")
            return {"response": f"🎉 Git 完整工作流完成!\n\n✅ 已推送到 origin/{branch}", "git_push_success": True, "git_push_branch": branch}
        else:
            error_msg = result.get("error", "git push 失败")
            print(f"[Git Push] ❌ {error_msg}")
            return {"response": f"❌ Git push 失败: {error_msg}", "git_push_success": False, "error": error_msg}
    except Exception as e:
        print(f"[Git Push] ❌ 异常: {e}")
        return {"response": f"❌ Git push 执行失败: {str(e)}", "git_push_success": False, "error": str(e)}
