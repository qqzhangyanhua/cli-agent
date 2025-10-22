#!/usr/bin/env python3
"""
安装测试脚本 - 验证 DNM CLI 是否正确安装

使用方法:
    python test_install.py
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def print_status(emoji: str, message: str, success: bool = None):
    """打印测试状态"""
    colors = {
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "cyan": "\033[96m",
        "reset": "\033[0m",
    }
    
    if success is True:
        color = colors["green"]
    elif success is False:
        color = colors["red"]
    else:
        color = colors["cyan"]
    
    print(f"{color}{emoji} {message}{colors['reset']}")


def test_python_version():
    """测试 Python 版本"""
    print_status("🐍", "检测 Python 版本...")
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    if version.major >= 3 and version.minor >= 8:
        print_status("✅", f"Python 版本: {version_str}", True)
        return True
    else:
        print_status("❌", f"Python 版本过低: {version_str} (需要 3.8+)", False)
        return False


def test_pip():
    """测试 pip 是否可用"""
    print_status("📦", "检测 pip...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=5
        )
        if result.returncode == 0:
            print_status("✅", f"pip 可用: {result.stdout.strip()}", True)
            return True
        else:
            print_status("❌", "pip 不可用", False)
            return False
    except Exception as e:
        print_status("❌", f"pip 检测失败: {e}", False)
        return False


def test_dependencies():
    """测试依赖是否安装"""
    print_status("📚", "检测依赖包...")
    
    required_packages = [
        "langgraph",
        "langchain_core",
        "langchain_openai",
    ]
    
    all_installed = True
    
    for package in required_packages:
        try:
            __import__(package)
            print_status("  ✅", f"{package} 已安装", True)
        except ImportError:
            print_status("  ❌", f"{package} 未安装", False)
            all_installed = False
    
    return all_installed


def get_dnm_command():
    """获取 dnm 命令路径"""
    system = platform.system()
    
    # 尝试在 PATH 中查找
    if system == "Windows":
        try:
            result = subprocess.run(
                ["where", "dnm"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=5
            )
            if result.returncode == 0:
                return "dnm"
        except:
            pass
        
        # 尝试默认安装位置
        default_path = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "dnm" / "dnm.bat"
        if default_path.exists():
            return str(default_path)
    else:
        try:
            result = subprocess.run(
                ["which", "dnm"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=5
            )
            if result.returncode == 0:
                return "dnm"
        except:
            pass
        
        # 尝试默认安装位置
        default_path = Path.home() / ".local" / "bin" / "dnm"
        if default_path.exists():
            return str(default_path)
    
    return None


def test_dnm_command():
    """测试 dnm 命令是否可用"""
    print_status("🔍", "检测 dnm 命令...")
    
    dnm_cmd = get_dnm_command()
    
    if not dnm_cmd:
        print_status("❌", "找不到 dnm 命令", False)
        print_status("💡", "提示: 可能需要配置 PATH 或重新打开终端", None)
        return False
    
    print_status("✅", f"找到 dnm: {dnm_cmd}", True)
    
    # 测试版本命令
    try:
        result = subprocess.run(
            [dnm_cmd, "--version"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=10
        )
        
        if result.returncode == 0:
            version = result.stdout.strip()
            print_status("✅", f"dnm 版本: {version}", True)
            return True
        else:
            error = result.stderr.strip() if result.stderr else "未知错误"
            print_status("❌", f"dnm 运行失败: {error}", False)
            return False
    except subprocess.TimeoutExpired:
        print_status("❌", "dnm 命令超时", False)
        return False
    except Exception as e:
        print_status("❌", f"测试 dnm 失败: {e}", False)
        return False


def test_path_configuration():
    """测试 PATH 配置"""
    print_status("🔧", "检测 PATH 配置...")
    
    system = platform.system()
    
    if system == "Windows":
        install_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "dnm"
    else:
        install_dir = Path.home() / ".local" / "bin"
    
    path = os.environ.get("PATH", "")
    
    if str(install_dir) in path:
        print_status("✅", f"安装目录已在 PATH 中: {install_dir}", True)
        return True
    else:
        print_status("⚠️", f"安装目录不在 PATH 中: {install_dir}", None)
        print_status("💡", "提示: 需要配置 PATH 或重新打开终端", None)
        return False


def test_config_directory():
    """测试配置目录"""
    print_status("📁", "检测配置目录...")
    
    system = platform.system()
    
    if system == "Windows":
        config_dir = Path(os.environ.get("APPDATA", "")) / "dnm"
    else:
        config_dir = Path.home() / ".config" / "dnm"
    
    if config_dir.exists():
        print_status("✅", f"配置目录存在: {config_dir}", True)
        return True
    else:
        print_status("⚠️", f"配置目录不存在: {config_dir}", None)
        print_status("💡", "提示: 首次运行时会自动创建", None)
        return True  # 不影响安装


def print_summary(results: dict):
    """打印测试摘要"""
    print("\n" + "=" * 60)
    print_status("📊", "测试摘要:", None)
    print("=" * 60)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print("-" * 60)
    print(f"  总计: {total} | 通过: {passed} | 失败: {failed}")
    print("=" * 60)
    
    if failed == 0:
        print_status("🎉", "所有测试通过！安装成功！", True)
        print()
        print_status("💡", "下一步:", None)
        print("  1. 运行: dnm --help")
        print("  2. 进入交互模式: dnm")
        print("  3. 或执行命令: dnm \"列出所有文件\"")
    else:
        print_status("⚠️", f"有 {failed} 项测试未通过", False)
        print()
        print_status("💡", "建议:", None)
        
        if not results.get("Python 版本"):
            print("  • 升级 Python 到 3.8 或更高版本")
        
        if not results.get("依赖包"):
            print("  • 运行: pip install --user langgraph langchain-core langchain-openai")
        
        if not results.get("dnm 命令"):
            print("  • 检查安装是否成功")
            print("  • 配置 PATH 环境变量")
            print("  • 重新打开终端")
            print("  • 或使用完整路径运行 dnm")
    
    return failed == 0


def main():
    """主函数"""
    print("=" * 60)
    print_status("🧪", "DNM CLI 安装测试", None)
    print("=" * 60)
    print()
    
    # 显示系统信息
    print_status("💻", f"系统: {platform.system()} {platform.release()}", None)
    print_status("🏠", f"用户: {os.environ.get('USERNAME', os.environ.get('USER', '未知'))}", None)
    print()
    
    # 运行测试
    results = {}
    
    results["Python 版本"] = test_python_version()
    print()
    
    results["pip"] = test_pip()
    print()
    
    results["依赖包"] = test_dependencies()
    print()
    
    results["PATH 配置"] = test_path_configuration()
    print()
    
    results["配置目录"] = test_config_directory()
    print()
    
    results["dnm 命令"] = test_dnm_command()
    
    # 打印摘要
    success = print_summary(results)
    
    return 0 if success else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n👋 测试已取消")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)


