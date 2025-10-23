#!/usr/bin/env python3
"""
安装 prompt-toolkit 以启用智能文件引用功能

这个脚本会检测并安装 prompt-toolkit，为 @ 文件引用功能
提供 IDE 风格的自动补全体验。
"""

import sys
import subprocess


def check_installed():
    """检查 prompt-toolkit 是否已安装"""
    try:
        import prompt_toolkit
        return True, prompt_toolkit.__version__
    except ImportError:
        return False, None


def install_package():
    """安装 prompt-toolkit"""
    print("📦 正在安装 prompt-toolkit...")
    print()
    
    try:
        # 使用 pip 安装
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "prompt-toolkit>=3.0.0"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ 安装成功！\n")
            return True
        else:
            print(f"❌ 安装失败\n")
            print(f"错误信息:\n{result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 安装过程中出现错误: {e}\n")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 智能文件引用功能 - prompt-toolkit 安装器")
    print("=" * 60)
    print()
    
    # 检查是否已安装
    is_installed, version = check_installed()
    
    if is_installed:
        print(f"✅ prompt-toolkit 已安装")
        print(f"   版本: {version}")
        print()
        print("💡 你已经可以使用增强的 @ 文件引用功能了！")
        print()
        print("🎯 试试看:")
        print("   1. 运行 'dnm' 或 'ai-agent'")
        print("   2. 输入 '@' 后继续输入文件名")
        print("   3. 使用上下箭头选择文件")
        print("   4. 按 Enter 确认")
        print()
        return 0
    
    # 提示安装
    print("⚠️  prompt-toolkit 未安装")
    print()
    print("🌟 安装后你将获得:")
    print("   • IDE 风格的自动补全")
    print("   • 实时文件搜索和过滤")
    print("   • 历史命令记录和建议")
    print("   • 更流畅的输入体验")
    print()
    
    # 询问是否安装
    try:
        choice = input("是否现在安装? (Y/n): ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\n\n👋 已取消\n")
        return 1
    
    if choice in ['', 'y', 'yes', '是']:
        print()
        success = install_package()
        
        if success:
            # 再次检查
            is_installed, version = check_installed()
            if is_installed:
                print(f"🎉 安装完成！版本: {version}")
                print()
                print("🎯 现在可以使用增强功能了:")
                print("   运行 'dnm' 或 'ai-agent' 开始体验")
                print()
                print("📚 查看使用指南:")
                print("   cat docs/SMART_FILE_REFERENCE.md")
                print("   cat UPGRADE_GUIDE.md")
                print()
                return 0
            else:
                print("⚠️  安装可能未成功，请手动检查")
                print()
                print("💡 手动安装命令:")
                print("   pip install prompt-toolkit>=3.0.0")
                print()
                return 1
        else:
            print("💡 手动安装命令:")
            print("   pip install prompt-toolkit>=3.0.0")
            print()
            return 1
    else:
        print()
        print("👌 已跳过安装")
        print()
        print("💡 你仍然可以使用传统的文件选择器模式")
        print("   稍后如需安装，运行:")
        print("   python install_prompt_toolkit.py")
        print()
        return 0


if __name__ == "__main__":
    sys.exit(main())

