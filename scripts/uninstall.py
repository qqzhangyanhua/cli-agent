#!/usr/bin/env python3
"""
AI Agent CLI 跨平台卸载脚本

支持 Windows、macOS 和 Linux 系统的自动卸载

使用方法:
    python uninstall.py                  # 默认卸载
    python uninstall.py --dir /path/to/dir # 从自定义目录卸载
"""

import os
import sys
import shutil
import argparse
import platform
from pathlib import Path


def print_step(emoji: str, message: str, color: str = None):
    """打印带格式的步骤信息"""
    colors = {
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "cyan": "\033[96m",
        "reset": "\033[0m",
    }
    
    if color and color in colors:
        print(f"{colors[color]}{emoji} {message}{colors['reset']}")
    else:
        print(f"{emoji} {message}")


def get_default_install_dir() -> Path:
    """获取默认安装目录"""
    system = platform.system()
    
    if system == "Windows":
        return Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))) / "Programs" / "dnm"
    else:
        return Path.home() / ".local" / "bin"


def get_config_dir() -> Path:
    """获取配置目录"""
    system = platform.system()
    
    if system == "Windows":
        return Path(os.environ.get("APPDATA", os.path.expanduser("~\\AppData\\Roaming"))) / "dnm"
    else:
        return Path.home() / ".config" / "dnm"


def remove_files(install_dir: Path):
    """删除安装的文件"""
    if not install_dir.exists():
        print_step("⚠️", f"安装目录不存在: {install_dir}", "yellow")
        print("可能已经卸载或从未安装")
        return False
    
    # 主程序文件
    main_files = ["dnm", "ai-agent", "dnm.bat", "ai-agent.bat"]

    # 配置文件
    config_files = ["mcp_config.json", "requirements.txt", "INSTALL_MODULES.txt"]

    all_files = main_files + config_files
    removed_count = 0

    # 删除文件
    for file_name in all_files:
        file_path = install_dir / file_name
        if file_path.exists():
            try:
                file_path.unlink()
                print_step("🗑️", f"删除: {file_path}", "yellow")
                removed_count += 1
            except Exception as e:
                print_step("❌", f"无法删除 {file_path}: {e}", "red")

    # 删除 src 目录
    src_dir = install_dir / "src"
    if src_dir.exists():
        try:
            shutil.rmtree(src_dir)
            print_step("🗑️", f"删除: {src_dir}", "yellow")
            removed_count += 1
        except Exception as e:
            print_step("❌", f"无法删除 {src_dir}: {e}", "red")
    
    # 如果是专门的 dnm 目录且为空，删除目录
    if install_dir.name == "dnm":
        try:
            remaining = list(install_dir.iterdir())
            if not remaining:
                install_dir.rmdir()
                print_step("🗑️", f"删除空安装目录: {install_dir}", "yellow")
            elif len(remaining) > 0:
                print_step("⚠️", f"安装目录不为空，保留: {install_dir}", "yellow")
        except Exception as e:
            print_step("⚠️", f"无法删除目录 {install_dir}: {e}", "yellow")
    
    return removed_count > 0


def remove_config(config_dir: Path, force: bool = False):
    """删除配置目录"""
    if not config_dir.exists():
        return False
    
    if force:
        response = "y"
    else:
        try:
            response = input(f"\n是否删除配置目录 {config_dir}? (y/N) ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            return False
    
    if response == "y":
        try:
            shutil.rmtree(config_dir)
            print_step("🗑️", f"删除配置目录: {config_dir}", "yellow")
            return True
        except Exception as e:
            print_step("❌", f"无法删除配置目录: {e}", "red")
            return False
    
    return False


def print_path_reminder(install_dir: Path):
    """提醒用户删除 PATH 配置"""
    print()
    print_step("💡", "提示: 如果之前手动添加了 PATH，请记得删除:", "cyan")
    print(f"   {install_dir}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="AI Agent CLI 跨平台卸载脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--dir",
        type=str,
        help="自定义安装目录"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制删除，不询问确认"
    )
    
    parser.add_argument(
        "--keep-config",
        action="store_true",
        help="保留配置目录"
    )
    
    args = parser.parse_args()
    
    print_step("🗑️", "开始卸载 DNM CLI...", "yellow")
    print()
    
    # 确定安装目录
    if args.dir:
        install_dir = Path(args.dir).absolute()
    else:
        install_dir = get_default_install_dir()
    
    print_step("📦", f"卸载目录: {install_dir}", "cyan")
    print()
    
    # 删除文件
    files_removed = remove_files(install_dir)
    
    # 删除配置
    config_dir = get_config_dir()
    if not args.keep_config:
        remove_config(config_dir, force=args.force)
    
    # 完成
    print()
    if files_removed:
        print_step("✅", "卸载完成！", "green")
        print_path_reminder(install_dir)
    else:
        print_step("⚠️", "未找到需要卸载的文件", "yellow")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_step("👋", "卸载已取消", "yellow")
        sys.exit(130)
    except Exception as e:
        print()
        print_step("❌", f"卸载失败: {e}", "red")
        sys.exit(1)



