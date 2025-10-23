#!/usr/bin/env python3
"""
智能文件引用功能演示

这个脚本演示新的 @ 文件引用功能的各种特性
"""

import sys
import os
from pathlib import Path

# 添加项目目录到路径
SCRIPT_DIR = Path(__file__).parent.absolute()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from smart_file_input import SmartFileInput, check_prompt_toolkit_available


def print_welcome():
    """打印欢迎信息"""
    print("\n" + "=" * 70)
    print("🎮 智能文件引用功能 - 交互式演示")
    print("=" * 70)
    print()
    
    if check_prompt_toolkit_available():
        print("✅ 增强模式已启用 (prompt-toolkit)")
        print()
        print("🎯 功能特性:")
        print("   • 输入 @ 后自动显示文件补全列表")
        print("   • 实时模糊搜索和过滤")
        print("   • 上下箭头选择文件")
        print("   • Tab 键补全，Enter 确认")
        print("   • 自动保存历史记录")
        print()
    else:
        print("⚠️  降级模式 (基础输入)")
        print()
        print("💡 提示: 安装 prompt-toolkit 获得更好体验")
        print("   pip install prompt-toolkit>=3.0.0")
        print()
    
    print("📝 演示场景:")
    print("   1. 基础文件引用: '@README.md 总结这个文档'")
    print("   2. 模糊搜索: '@cfg' 匹配 agent_config.py")
    print("   3. 多文件引用: '比较 @old 和 @new'")
    print("   4. 路径引用: '@docs/README.md'")
    print()
    print("💡 提示:")
    print("   • 输入 'demo1', 'demo2' 等查看预设演示")
    print("   • 输入 'help' 查看所有命令")
    print("   • 输入 'exit' 退出演示")
    print()
    print("=" * 70)
    print()


def show_help():
    """显示帮助信息"""
    print()
    print("📚 可用命令:")
    print("-" * 60)
    print("  demo1    - 演示基础文件引用")
    print("  demo2    - 演示模糊搜索")
    print("  demo3    - 演示多文件引用")
    print("  demo4    - 演示路径引用")
    print("  test     - 自由测试模式")
    print("  help     - 显示此帮助")
    print("  exit     - 退出演示")
    print("-" * 60)
    print()


def run_demo1(smart_input):
    """演示1: 基础文件引用"""
    print()
    print("📌 演示 1: 基础文件引用")
    print("-" * 60)
    print("场景: 引用 README.md 并提问")
    print()
    print("请尝试输入: @README.md 总结这个项目")
    print("(或者输入 @read 然后使用上下箭头选择)")
    print()
    
    try:
        user_input = smart_input.get_input("👤 你: ")
        print()
        print(f"✅ 收到输入: {user_input}")
        
        if '@' in user_input:
            import re
            files = re.findall(r'@([^\s]+)', user_input)
            if files:
                print(f"📁 检测到文件引用: {', '.join(files)}")
        print()
        
    except (KeyboardInterrupt, EOFError):
        print("\n")


def run_demo2(smart_input):
    """演示2: 模糊搜索"""
    print()
    print("📌 演示 2: 模糊搜索")
    print("-" * 60)
    print("场景: 使用缩写快速找到文件")
    print()
    print("尝试以下输入:")
    print("  • @cfg  → 匹配 agent_config.py")
    print("  • @wkf  → 匹配 agent_workflow.py")
    print("  • @ui   → 匹配 agent_ui.py")
    print()
    
    try:
        user_input = smart_input.get_input("👤 你: ")
        print()
        print(f"✅ 收到输入: {user_input}")
        print()
        
    except (KeyboardInterrupt, EOFError):
        print("\n")


def run_demo3(smart_input):
    """演示3: 多文件引用"""
    print()
    print("📌 演示 3: 多文件引用")
    print("-" * 60)
    print("场景: 同时引用多个文件")
    print()
    print("请尝试输入: 比较 @agent_config.py 和 @agent_llm.py")
    print()
    
    try:
        user_input = smart_input.get_input("👤 你: ")
        print()
        print(f"✅ 收到输入: {user_input}")
        
        if '@' in user_input:
            import re
            files = re.findall(r'@([^\s]+)', user_input)
            if files:
                print(f"📁 检测到 {len(files)} 个文件引用: {', '.join(files)}")
        print()
        
    except (KeyboardInterrupt, EOFError):
        print("\n")


def run_demo4(smart_input):
    """演示4: 路径引用"""
    print()
    print("📌 演示 4: 路径引用")
    print("-" * 60)
    print("场景: 引用子目录中的文件")
    print()
    print("请尝试输入: @docs/README.md 或 @test/test_demo.py")
    print()
    
    try:
        user_input = smart_input.get_input("👤 你: ")
        print()
        print(f"✅ 收到输入: {user_input}")
        print()
        
    except (KeyboardInterrupt, EOFError):
        print("\n")


def free_test_mode(smart_input):
    """自由测试模式"""
    print()
    print("🎮 自由测试模式")
    print("-" * 60)
    print("现在可以自由测试 @ 文件引用功能")
    print("输入 'back' 返回主菜单")
    print()
    
    while True:
        try:
            user_input = smart_input.get_input("👤 你: ")
            
            if user_input.lower() in ['back', '返回']:
                print()
                break
            
            print()
            print(f"✅ 收到输入: {user_input}")
            
            if '@' in user_input:
                import re
                files = re.findall(r'@([^\s]+)', user_input)
                if files:
                    print(f"📁 检测到文件引用: {', '.join(files)}")
            print()
            
        except (KeyboardInterrupt, EOFError):
            print("\n")
            break


def main():
    """主函数"""
    print_welcome()
    
    # 创建智能输入实例
    smart_input = SmartFileInput()
    
    # 主循环
    while True:
        try:
            command = input("🎯 请选择演示 (输入 help 查看帮助): ").strip().lower()
            
            if not command:
                continue
            
            if command in ['exit', 'quit', 'q', '退出']:
                print("\n👋 感谢体验！\n")
                print("💡 提示: 运行 'dnm' 或 'ai-agent' 体验完整功能\n")
                break
            
            elif command == 'help':
                show_help()
            
            elif command == 'demo1':
                run_demo1(smart_input)
            
            elif command == 'demo2':
                run_demo2(smart_input)
            
            elif command == 'demo3':
                run_demo3(smart_input)
            
            elif command == 'demo4':
                run_demo4(smart_input)
            
            elif command == 'test':
                free_test_mode(smart_input)
            
            else:
                print(f"\n❌ 未知命令: {command}")
                print("💡 输入 'help' 查看可用命令\n")
        
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 演示已结束\n")
            break
        except Exception as e:
            print(f"\n❌ 出错: {e}\n")


if __name__ == "__main__":
    main()

