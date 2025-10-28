#!/usr/bin/env python3
"""
AI Agent CLI 跨平台安装脚本

支持 Windows、macOS 和 Linux 系统的自动安装

使用方法:
    python install.py                    # 默认安装
    python install.py --dir /path/to/dir # 自定义安装目录
    python install.py --user             # 仅用户安装（不需要管理员权限）
"""

import os
import sys
import shutil
import subprocess
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


def check_python():
    """检查 Python 版本"""
    print_step("🐍", "检查Python环境...", "yellow")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_step("❌", f"错误: 需要 Python 3.8+，当前版本 {version.major}.{version.minor}", "red")
        sys.exit(1)
    
    print_step("✅", f"Python版本: {version.major}.{version.minor}.{version.micro}", "green")
    return True


def install_dependencies(script_dir: Path):
    """安装 Python 依赖"""
    print()
    print_step("📦", "安装Python依赖...", "yellow")
    
    requirements_file = script_dir / "requirements.txt"
    if not requirements_file.exists():
        print_step("⚠️", "未找到 requirements.txt，跳过依赖安装", "yellow")
        return False
    
    print("正在安装依赖包...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file), "--user", "--quiet"],
            check=True,
            capture_output=True,
            encoding='utf-8',
            errors='replace'
        )
        print_step("✅", "依赖安装成功", "green")
        return True
    except subprocess.CalledProcessError as e:
        print_step("⚠️", "依赖安装可能有问题，但继续安装...", "yellow")
        print_step("💡", "请手动运行: python -m pip install --user langgraph langchain-core langchain-openai", "cyan")
        return False


def get_default_install_dir() -> Path:
    """获取默认安装目录"""
    system = platform.system()
    
    if system == "Windows":
        # Windows: %LOCALAPPDATA%\Programs\dnm
        return Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))) / "Programs" / "dnm"
    else:
        # Unix-like: ~/.local/bin
        return Path.home() / ".local" / "bin"


def get_config_dir() -> Path:
    """获取配置目录"""
    system = platform.system()
    
    if system == "Windows":
        return Path(os.environ.get("APPDATA", os.path.expanduser("~\\AppData\\Roaming"))) / "dnm"
    else:
        return Path.home() / ".config" / "dnm"


def copy_files(script_dir: Path, install_dir: Path, config_dir: Path):
    """复制文件到安装目录"""
    print()
    print_step("📋", "复制程序文件...", "yellow")
    
    # 创建安装目录
    install_dir.mkdir(parents=True, exist_ok=True)
    
    # 复制主程序
    main_files = ["dnm", "ai-agent"]
    for file_name in main_files:
        source = script_dir / file_name
        if source.exists():
            shutil.copy2(source, install_dir)
            # Unix-like 系统需要设置可执行权限
            if platform.system() != "Windows":
                (install_dir / file_name).chmod(0o755)
    
    # 复制模块文件 - 使用新的目录结构
    print_step("📦", "复制模块文件...", "yellow")

    # 复制 src 目录及其所有子目录
    src_dir = script_dir / "src"
    if src_dir.exists():
        dest_src_dir = install_dir / "src"
        if dest_src_dir.exists():
            shutil.rmtree(dest_src_dir)
        shutil.copytree(src_dir, dest_src_dir)
        print_step("✅", "已复制 src/ 目录", "green")
    else:
        print_step("❌", "错误: 找不到 src/ 目录", "red")
        sys.exit(1)

    # 复制配置文件
    config_files = ["mcp_config.json", "requirements.txt", "INSTALL_MODULES.txt"]
    for config_file in config_files:
        source = script_dir / config_file
        if source.exists():
            shutil.copy2(source, install_dir)
        else:
            print_step("⚠️", f"警告: 找不到 {config_file}", "yellow")
    
    # 🔧 复制 config.json 到全局配置目录（关键步骤）
    config_source = script_dir / "config.json"
    config_dest = config_dir / "config.json"
    
    if config_source.exists():
        print_step("📝", "复制 config.json 到全局配置目录...", "yellow")
        shutil.copy2(config_source, config_dest)
        print_step("✅", f"已复制 config.json 到 {config_dest}", "green")
        print_step("💡", "现在可以在任何目录使用 dnm 命令", "cyan")
    else:
        # 如果没有 config.json，则复制模板文件
        template_source = script_dir / "config.template.json"
        if template_source.exists():
            print_step("⚠️", "未找到 config.json，复制模板文件", "yellow")
            shutil.copy2(template_source, config_dest)
            print_step("💡", f"请编辑 {config_dest} 填入你的 API 密钥", "cyan")
        else:
            print_step("❌", "错误: 找不到 config.json 或 config.template.json", "red")
            sys.exit(1)
    
    # Windows 特殊处理：创建批处理启动器
    if platform.system() == "Windows":
        create_windows_launcher(install_dir)


def create_windows_launcher(install_dir: Path):
    """为 Windows 创建批处理启动器"""
    dnm_bat = install_dir / "dnm.bat"
    dnm_py = install_dir / "dnm"
    
    bat_content = f'@echo off\npython "{dnm_py}" %*\n'
    dnm_bat.write_text(bat_content, encoding="ascii")
    
    # 同样为 ai-agent 创建
    ai_agent_bat = install_dir / "ai-agent.bat"
    ai_agent_py = install_dir / "ai-agent"
    if ai_agent_py.exists():
        bat_content = f'@echo off\npython "{ai_agent_py}" %*\n'
        ai_agent_bat.write_text(bat_content, encoding="ascii")


def setup_path(install_dir: Path):
    """设置 PATH 环境变量"""
    print()
    print_step("🔍", "检查 PATH 配置...", "yellow")
    
    install_dir_str = str(install_dir)
    current_path = os.environ.get("PATH", "")
    
    # 检查是否已在 PATH 中
    if install_dir_str in current_path.split(os.pathsep):
        print_step("✅", f"{install_dir_str} 已在 PATH 中", "green")
        return True
    
    print_step("⚠️", f"{install_dir} 不在 PATH 中", "yellow")
    
    system = platform.system()
    
    if system == "Windows":
        print()
        print("请将以下目录添加到你的 PATH 环境变量:")
        print()
        print_step("📍", f"  {install_dir}", "cyan")
        print()
        print("添加方法:")
        print("  1. 右键 '此电脑' -> '属性' -> '高级系统设置'")
        print("  2. 点击 '环境变量'")
        print("  3. 在 '用户变量' 中找到 'Path' 并编辑")
        print("  4. 点击 '新建'，添加上述路径")
        print("  5. 点击 '确定' 保存")
        print()
        print_step("💡", "或者在 PowerShell 中运行 (管理员权限):", "cyan")
        print(f'  [Environment]::SetEnvironmentVariable("Path", $env:Path + ";{install_dir}", "User")')
        
    else:  # Unix-like
        shell = os.environ.get("SHELL", "")
        
        if "zsh" in shell:
            config_file = Path.home() / ".zshrc"
        elif "bash" in shell:
            config_file = Path.home() / ".bashrc"
        else:
            config_file = Path.home() / ".profile"
        
        print()
        print(f"请将以下内容添加到你的 shell 配置文件 ({config_file}):")
        print()
        print_step("📍", f'  export PATH="${{HOME}}/.local/bin:${{PATH}}"', "cyan")
        print()
        print(f"然后执行: source {config_file}")
    
    return False


def test_installation(install_dir: Path):
    """测试安装"""
    print()
    print_step("🧪", "测试安装...", "yellow")
    
    system = platform.system()
    if system == "Windows":
        dnm_cmd = install_dir / "dnm.bat"
    else:
        dnm_cmd = install_dir / "dnm"
    
    if not dnm_cmd.exists():
        print_step("❌", "安装失败: 找不到 dnm 命令", "red")
        return False
    
    try:
        result = subprocess.run(
            [str(dnm_cmd), "--version"],
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            timeout=5
        )
        if result.returncode == 0:
            print_step("✅", "安装测试成功！", "green")
            return True
        else:
            print_step("⚠️", "安装测试失败，可能需要手动检查依赖", "yellow")
            print_step("💡", "请尝试运行: pip install --user langgraph langchain-core langchain-openai", "cyan")
            return False
    except Exception as e:
        print_step("⚠️", f"安装测试失败: {e}", "yellow")
        print_step("💡", "请尝试运行: pip install --user langgraph langchain-core langchain-openai", "cyan")
        return False


def create_config_dir():
    """创建配置目录"""
    config_dir = get_config_dir()
    if not config_dir.exists():
        print_step("📁", f"创建配置目录: {config_dir}", "yellow")
        config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def print_usage_info():
    """打印使用说明"""
    print()
    print_step("✅", "DNM 安装完成！", "green")
    print()
    print_step("📖", "使用方法:", "cyan")
    print("   dnm                      # 进入交互模式")
    print('   dnm "列出所有文件"        # 执行单条命令')
    print("   dnm --help               # 查看帮助")
    print("   dnm files                # 查看@文件引用功能")
    print()
    print_step("🎯", "新功能:", "cyan")
    print("   • 输入 @ 启动交互式文件选择器")
    print("   • 输入 @文件名 快速搜索文件")
    print("   • 支持自然语言文件操作")
    print()
    print_step("🎉", "享受使用 DNM!", "green")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="AI Agent CLI 跨平台安装脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--dir",
        type=str,
        help="自定义安装目录"
    )
    
    parser.add_argument(
        "--user",
        action="store_true",
        help="仅用户安装（不需要管理员权限）"
    )
    
    parser.add_argument(
        "--skip-deps",
        action="store_true",
        help="跳过依赖安装"
    )
    
    args = parser.parse_args()
    
    print_step("🚀", "开始安装 DNM CLI...", "green")
    print()
    
    # 获取脚本所在目录
    script_dir = Path(__file__).parent.absolute()
    
    # 检查 Python 环境
    check_python()
    
    # 安装依赖
    if not args.skip_deps:
        install_dependencies(script_dir)
    
    # 确定安装目录
    if args.dir:
        install_dir = Path(args.dir).absolute()
    else:
        install_dir = get_default_install_dir()
    
    print()
    print_step("📦", "安装信息:", "cyan")
    print(f"   源目录: {script_dir}")
    print(f"   安装目录: {install_dir}")
    print(f"   系统: {platform.system()} {platform.release()}")
    
    # 创建配置目录
    config_dir = create_config_dir()
    
    # 复制文件
    copy_files(script_dir, install_dir, config_dir)
    
    # 设置 PATH
    path_ok = setup_path(install_dir)
    
    # 测试安装
    test_installation(install_dir)
    
    # 打印使用说明
    print_usage_info()
    
    if not path_ok:
        print()
        print_step("💡", "提示: 请按照上述说明配置 PATH，然后重新打开终端", "yellow")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_step("👋", "安装已取消", "yellow")
        sys.exit(130)
    except Exception as e:
        print()
        print_step("❌", f"安装失败: {e}", "red")
        sys.exit(1)


