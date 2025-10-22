#!/usr/bin/env python3
"""
Windows 编码兼容性测试脚本
测试所有 subprocess 调用是否正确处理编码
"""

import sys
import subprocess
from pathlib import Path


def print_test(name: str, passed: bool):
    """打印测试结果"""
    icon = "✅" if passed else "❌"
    status = "通过" if passed else "失败"
    print(f"{icon} {name}: {status}")


def test_git_encoding():
    """测试 Git 命令编码"""
    print("\n📝 测试 1: Git 命令编码")
    print("-" * 60)
    
    try:
        from git_tools import git_tools
        
        # 测试 check_git_repo
        is_repo = git_tools.check_git_repo()
        print_test("check_git_repo", True)
        
        if not is_repo:
            print("   ⚠️ 当前目录不是 Git 仓库，跳过其他 Git 测试")
            return True
        
        # 测试 get_git_status
        status = git_tools.get_git_status()
        print_test("get_git_status", status["success"])
        
        # 测试 get_git_diff
        diff = git_tools.get_git_diff(staged=False)
        print_test("get_git_diff (unstaged)", diff["success"])
        
        diff_staged = git_tools.get_git_diff(staged=True)
        print_test("get_git_diff (staged)", diff_staged["success"])
        
        # 测试 get_recent_commits
        commits = git_tools.get_recent_commits(5)
        print_test("get_recent_commits", commits["success"])
        
        # 测试 analyze_changes
        analysis = git_tools.analyze_changes()
        # 没有变更也算成功
        print_test("analyze_changes", True)
        
        return True
    
    except UnicodeDecodeError as e:
        print_test("Git 编码测试", False)
        print(f"   编码错误: {e}")
        return False
    except Exception as e:
        print_test("Git 编码测试", False)
        print(f"   异常: {e}")
        return False


def test_terminal_command_encoding():
    """测试终端命令编码"""
    print("\n💻 测试 2: 终端命令编码")
    print("-" * 60)
    
    try:
        from agent_utils import execute_terminal_command
        
        # 测试简单命令
        result = execute_terminal_command("echo Hello")
        print_test("execute_terminal_command (echo)", result["success"])
        
        # 测试带中文的命令
        result = execute_terminal_command("echo 你好世界")
        print_test("execute_terminal_command (中文)", result["success"])
        
        return True
    
    except UnicodeDecodeError as e:
        print_test("终端命令编码测试", False)
        print(f"   编码错误: {e}")
        return False
    except Exception as e:
        print_test("终端命令编码测试", False)
        print(f"   异常: {e}")
        return False


def test_env_diagnostic_encoding():
    """测试环境诊断编码"""
    print("\n🔍 测试 3: 环境诊断编码")
    print("-" * 60)
    
    try:
        from env_diagnostic_tools import EnvironmentDiagnostic
        
        diagnostic = EnvironmentDiagnostic(".")
        
        # 测试 Python 环境检查
        py_env = diagnostic.check_python_env()
        print_test("check_python_env", "python_version" in py_env)
        
        # 测试依赖检查
        deps = diagnostic.check_dependencies()
        print_test("check_dependencies", "requirements_file" in deps)
        
        # 测试开发工具检查
        dev_tools = diagnostic.check_dev_tools()
        print_test("check_dev_tools", "tools" in dev_tools)
        
        return True
    
    except UnicodeDecodeError as e:
        print_test("环境诊断编码测试", False)
        print(f"   编码错误: {e}")
        return False
    except Exception as e:
        print_test("环境诊断编码测试", False)
        print(f"   异常: {e}")
        return False


def test_subprocess_direct():
    """直接测试 subprocess 编码"""
    print("\n⚙️ 测试 4: subprocess 直接调用")
    print("-" * 60)
    
    tests = []
    
    # 测试 Git 命令
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=5
        )
        tests.append(("git --version", result.returncode == 0))
    except Exception as e:
        tests.append(("git --version", False))
    
    # 测试 Python 命令
    try:
        result = subprocess.run(
            [sys.executable, "--version"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=5
        )
        tests.append(("python --version", result.returncode == 0))
    except Exception as e:
        tests.append(("python --version", False))
    
    # 测试 pip 命令
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=5
        )
        tests.append(("pip --version", result.returncode == 0))
    except Exception as e:
        tests.append(("pip --version", False))
    
    for name, passed in tests:
        print_test(name, passed)
    
    return all(passed for _, passed in tests)


def main():
    """主函数"""
    print("=" * 60)
    print("🧪 Windows 编码兼容性测试")
    print("=" * 60)
    print(f"\n🖥️ 系统: {sys.platform}")
    print(f"🐍 Python: {sys.version}")
    print(f"📂 工作目录: {Path.cwd()}")
    
    # 运行所有测试
    results = []
    
    try:
        results.append(("Git 编码", test_git_encoding()))
    except Exception as e:
        print(f"\n❌ Git 编码测试异常: {e}")
        results.append(("Git 编码", False))
    
    try:
        results.append(("终端命令编码", test_terminal_command_encoding()))
    except Exception as e:
        print(f"\n❌ 终端命令编码测试异常: {e}")
        results.append(("终端命令编码", False))
    
    try:
        results.append(("环境诊断编码", test_env_diagnostic_encoding()))
    except Exception as e:
        print(f"\n❌ 环境诊断编码测试异常: {e}")
        results.append(("环境诊断编码", False))
    
    try:
        results.append(("subprocess 直接调用", test_subprocess_direct()))
    except Exception as e:
        print(f"\n❌ subprocess 直接调用测试异常: {e}")
        results.append(("subprocess 直接调用", False))
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        icon = "✅" if result else "❌"
        print(f"{icon} {name}")
    
    print("\n" + "-" * 60)
    print(f"通过: {passed}/{total}")
    print(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有测试通过！Windows 编码兼容性修复成功！")
        return 0
    else:
        print(f"\n⚠️ 有 {total - passed} 个测试失败，请检查")
        return 1


if __name__ == "__main__":
    sys.exit(main())

