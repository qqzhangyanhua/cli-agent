"""
Code Review 功能测试
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code_review_tools import perform_code_review_func, code_review_tool


def test_code_review_func():
    """测试代码审查函数"""
    print("=" * 80)
    print("🧪 测试 Code Review 功能")
    print("=" * 80)
    print()
    
    # 调用代码审查函数
    result = perform_code_review_func()
    
    print()
    print("=" * 80)
    print("📋 审查结果:")
    print("=" * 80)
    print(result)
    print()


def test_code_review_tool():
    """测试 LangChain Tool 封装"""
    print("=" * 80)
    print("🧪 测试 Code Review Tool")
    print("=" * 80)
    print()
    
    print("Tool 名称:", code_review_tool.name)
    print("Tool 描述:", code_review_tool.description)
    print()
    
    # 调用工具
    result = code_review_tool.func("")
    
    print()
    print("=" * 80)
    print("📋 Tool 调用结果:")
    print("=" * 80)
    print(result)
    print()


if __name__ == "__main__":
    print("\n" + "🔍" * 40)
    print("Code Review 功能测试")
    print("🔍" * 40 + "\n")
    
    # 测试1: 直接函数调用
    test_code_review_func()
    
    print("\n" + "─" * 80 + "\n")
    
    # 测试2: LangChain Tool 调用
    test_code_review_tool()
    
    print("\n" + "=" * 80)
    print("✅ 测试完成！")
    print("=" * 80)

