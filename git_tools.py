"""
Git工具模块
提供Git相关功能，如生成commit消息等
"""

import subprocess
from typing import Dict, Optional


class GitTools:
    """Git操作工具类"""

    def __init__(self, working_dir: str = "."):
        """
        初始化Git工具

        Args:
            working_dir: Git仓库路径
        """
        self.working_dir = working_dir

    def check_git_repo(self) -> bool:
        """检查当前目录是否是Git仓库"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_git_status(self) -> Dict:
        """
        获取Git状态

        Returns:
            {
                "success": bool,
                "status": str,
                "has_changes": bool,
                "error": str
            }
        """
        if not self.check_git_repo():
            return {
                "success": False,
                "error": "当前目录不是Git仓库",
                "has_changes": False,
            }

        try:
            result = subprocess.run(
                ["git", "status", "--short"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=5,
            )

            status_output = result.stdout.strip()
            has_changes = len(status_output) > 0

            return {
                "success": True,
                "status": status_output if status_output else "工作区干净",
                "has_changes": has_changes,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"获取Git状态失败: {str(e)}",
                "has_changes": False,
            }

    def get_git_diff(self, staged: bool = False) -> Dict:
        """
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
        """
        if not self.check_git_repo():
            return {
                "success": False,
                "error": "当前目录不是Git仓库",
                "has_diff": False,
                "diff": "",
                "files_changed": [],
            }

        try:
            # 获取diff
            cmd = ["git", "diff"]
            if staged:
                cmd.append("--cached")

            result = subprocess.run(
                cmd, cwd=self.working_dir, capture_output=True, text=True, timeout=10
            )

            diff_output = result.stdout.strip()
            has_diff = len(diff_output) > 0

            # 获取变更文件列表
            stat_cmd = ["git", "diff", "--stat"]
            if staged:
                stat_cmd.append("--cached")

            stat_result = subprocess.run(
                stat_cmd,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=5,
            )

            # 解析变更的文件
            files_changed = []
            if stat_result.stdout:
                for line in stat_result.stdout.split("\n"):
                    if "|" in line:
                        filename = line.split("|")[0].strip()
                        files_changed.append(filename)

            return {
                "success": True,
                "diff": diff_output,
                "has_diff": has_diff,
                "files_changed": files_changed,
                "type": "staged" if staged else "unstaged",
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"获取Git diff失败: {str(e)}",
                "has_diff": False,
                "diff": "",
                "files_changed": [],
            }

    def get_recent_commits(self, count: int = 5) -> Dict:
        """
        获取最近的commit记录

        Args:
            count: 获取的commit数量

        Returns:
            {
                "success": bool,
                "commits": list,
                "error": str
            }
        """
        if not self.check_git_repo():
            return {"success": False, "error": "当前目录不是Git仓库", "commits": []}

        try:
            result = subprocess.run(
                ["git", "log", f"-{count}", "--oneline", "--no-decorate"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=5,
            )

            commits = []
            if result.stdout:
                for line in result.stdout.strip().split("\n"):
                    if line:
                        commits.append(line)

            return {"success": True, "commits": commits}

        except Exception as e:
            return {
                "success": False,
                "error": f"获取commit历史失败: {str(e)}",
                "commits": [],
            }

    def analyze_changes(self) -> Dict:
        """
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
        """
        # 检查是否是Git仓库
        if not self.check_git_repo():
            return {"success": False, "error": "❌ 当前目录不是Git仓库"}

        # 获取状态
        status_result = self.get_git_status()
        if not status_result["success"]:
            return status_result

        # 如果没有变更
        if not status_result["has_changes"]:
            return {"success": False, "error": "⚠️ 工作区没有变更，无需生成commit消息"}

        # 获取unstaged diff
        unstaged_diff = self.get_git_diff(staged=False)

        # 获取staged diff
        staged_diff = self.get_git_diff(staged=True)

        # 获取最近的commits（用于参考风格）
        recent_commits = self.get_recent_commits(5)

        # 合并文件列表
        all_files = list(
            set(
                unstaged_diff.get("files_changed", [])
                + staged_diff.get("files_changed", [])
            )
        )

        # 生成摘要
        summary_parts = []
        if staged_diff.get("has_diff"):
            summary_parts.append(
                f"已暂存 {len(staged_diff.get('files_changed', []))} 个文件"
            )
        if unstaged_diff.get("has_diff"):
            summary_parts.append(
                f"未暂存 {len(unstaged_diff.get('files_changed', []))} 个文件"
            )

        summary = "、".join(summary_parts) if summary_parts else "有变更"

        return {
            "success": True,
            "status": status_result["status"],
            "unstaged_diff": unstaged_diff.get("diff", ""),
            "staged_diff": staged_diff.get("diff", ""),
            "files_changed": all_files,
            "recent_commits": recent_commits.get("commits", []),
            "summary": summary,
            "has_staged": staged_diff.get("has_diff", False),
            "has_unstaged": unstaged_diff.get("has_diff", False),
        }


# 全局实例
git_tools = GitTools()


# ============================================
# 测试代码
# ============================================

if __name__ == "__main__":
    print("🔍 Git工具测试")
    print("=" * 80)

    # 测试1: 检查是否是Git仓库
    print("\n1. 检查Git仓库:")
    is_repo = git_tools.check_git_repo()
    print(f"   {'✅' if is_repo else '❌'} {'是Git仓库' if is_repo else '不是Git仓库'}")

    if not is_repo:
        print("\n⚠️ 当前目录不是Git仓库，无法继续测试")
        exit(0)

    # 测试2: 获取Git状态
    print("\n2. 获取Git状态:")
    status = git_tools.get_git_status()
    if status["success"]:
        print(f"   ✅ 状态: {status['status'][:100]}...")
        print(f"   有变更: {status['has_changes']}")
    else:
        print(f"   ❌ {status['error']}")

    # 测试3: 获取diff
    print("\n3. 获取Git diff:")
    diff = git_tools.get_git_diff()
    if diff["success"]:
        print(f"   ✅ 有diff: {diff['has_diff']}")
        if diff["files_changed"]:
            print(f"   变更文件:")
            for f in diff["files_changed"][:5]:
                print(f"      - {f}")
    else:
        print(f"   ❌ {diff['error']}")

    # 测试4: 获取最近commits
    print("\n4. 最近的commits:")
    commits = git_tools.get_recent_commits(5)
    if commits["success"]:
        print(f"   ✅ 找到 {len(commits['commits'])} 个commit")
        for c in commits["commits"]:
            print(f"      {c}")
    else:
        print(f"   ❌ {commits['error']}")

    # 测试5: 分析变更
    print("\n5. 分析变更:")
    analysis = git_tools.analyze_changes()
    if analysis["success"]:
        print(f"   ✅ 分析完成")
        print(f"   摘要: {analysis['summary']}")
        print(f"   变更文件: {len(analysis['files_changed'])} 个")
        print(f"   已暂存: {analysis['has_staged']}")
        print(f"   未暂存: {analysis['has_unstaged']}")
    else:
        print(f"   ❌ {analysis['error']}")

    print("\n" + "=" * 80)
    print("测试完成！")
