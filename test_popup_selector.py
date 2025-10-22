#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试弹出式文件选择器
演示当有多个文件匹配时的弹出选择功能
"""

import sys
import os
from pathlib import Path

# 添加项目目录到路径
SCRIPT_DIR = Path(__file__).parent.absolute()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from smart_file_input import SmartFileInput, check_prompt_toolkit_available


def print_demo():
    """演示弹出式选择"""
    print("\n" + "=" * 70)
    print("🎮 弹出式文件选择器测试")
    print("=" * 70)
    print()
    print("💡 这个测试演示当有多个文件匹配时的弹出式选择功能")
    print()
    
    smart_input = SmartFileInput()
    
    # 测试场景
    test_cases = [
        "@agent",
        "@test",
        "@config",
    ]
    
    print("📝 测试用例:")
    for i, case in enumerate(test_cases, 1):
        print(f"   {i}. {case}")
    print()
    
    print("请手动测试:")
    print("  输入包含 @ 的文本，如果匹配多个文件会显示弹出选择")
    print("  输入 exit 退出")
    print()
    
    while True:
        try:
            user_input = input("👤 你: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit']:
                break
            
            # 处理输入
            result = smart_input._fallback_input(user_input)
            print(f"\n✅ 结果: {result}\n")
            
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 退出\n")
            break


if __name__ == "__main__":
    print_demo()
