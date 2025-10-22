#!/usr/bin/env python3
"""
Code Review 功能演示
展示如何使用代码审查功能
"""

import sys
from code_review_tools import perform_code_review_func, code_review_tool


def print_header(title: str):
    """打印标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def demo_direct_call():
    """演示1: 直接函数调用"""
    print_header("📋 演示 1: 直接函数调用")
    
    print("调用 perform_code_review_func()...")
    print("─" * 80)
    
    result = perform_code_review_func()
    
    print("\n" + "─" * 80)
    print("结果:")
    print("─" * 80)
    print(result)


def demo_tool_call():
    """演示2: LangChain Tool 调用"""
    print_header("📋 演示 2: LangChain Tool 调用")
    
    print(f"Tool 名称: {code_review_tool.name}")
    print(f"Tool 描述: {code_review_tool.description[:100]}...")
    print("\n调用 code_review_tool.func()...")
    print("─" * 80)
    
    result = code_review_tool.func("")
    
    print("\n" + "─" * 80)
    print("结果:")
    print("─" * 80)
    print(result)


def demo_cli_usage():
    """演示3: CLI 使用说明"""
    print_header("📋 演示 3: CLI 使用说明")
    
    print("在 CLI 交互式模式下，你可以使用以下命令：")
    print()
    print("启动 CLI:")
    print("  $ ./ai-agent")
    print()
    print("然后输入以下任意一种表述:")
    print("  • 对当前待提交的代码进行code-review")
    print("  • 代码审查")
    print("  • code review")
    print("  • 检查我的代码")
    print("  • 帮我review一下代码")
    print("  • 代码有什么问题吗")
    print()
    print("系统会自动识别意图并执行代码审查。")
    print()
    print("或者直接使用命令行:")
    print('  $ ./ai-agent "对当前代码进行code review"')


def main():
    """主函数"""
    print("\n" + "🔍" * 40)
    print("       Code Review 功能演示")
    print("🔍" * 40)
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        
        if mode == "direct":
            demo_direct_call()
        elif mode == "tool":
            demo_tool_call()
        elif mode == "cli":
            demo_cli_usage()
        else:
            print(f"\n❌ 未知模式: {mode}")
            print("\n用法:")
            print("  python demo_code_review.py [direct|tool|cli]")
            print()
            print("  direct - 直接函数调用演示")
            print("  tool   - LangChain Tool 调用演示")
            print("  cli    - CLI 使用说明")
            sys.exit(1)
    else:
        # 默认运行所有演示
        try:
            demo_direct_call()
        except Exception as e:
            print(f"\n❌ 演示 1 失败: {str(e)}")
        
        print("\n" + "─" * 80 + "\n")
        
        try:
            demo_tool_call()
        except Exception as e:
            print(f"\n❌ 演示 2 失败: {str(e)}")
        
        print("\n" + "─" * 80 + "\n")
        
        demo_cli_usage()
    
    print("\n" + "=" * 80)
    print("✅ 演示完成！")
    print("=" * 80 + "\n")
    
    print("💡 提示:")
    print("  - 确保当前目录是 Git 仓库")
    print("  - 确保有代码变更（使用 git status 检查）")
    print("  - 代码审查会分析 staged 和 unstaged 的所有变更")
    print()


if __name__ == "__main__":
    main()

