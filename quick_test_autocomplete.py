#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试自动补全功能
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.absolute()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from smart_file_input import SmartFileInput, check_prompt_toolkit_available


def main():
    print("=" * 70)
    print("🎯 自动补全功能测试")
    print("=" * 70)
    print()
    
    if not check_prompt_toolkit_available():
        print("❌ prompt-toolkit 未安装，正在安装...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "prompt-toolkit>=3.0.0"])
        print()
    
    print("✅ prompt-toolkit 已就绪")
    print()
    print("💡 使用说明:")
    print("   1. 输入 @ 会立即显示文件列表（如图片所示）")
    print("   2. 继续输入可以过滤文件")
    print("   3. 使用 ↑↓ 键选择文件")
    print("   4. 按 Tab 键补全，Enter 确认")
    print("   5. 按 Ctrl+C 退出")
    print()
    print("=" * 70)
    print()
    
    smart_input = SmartFileInput()
    
    print("开始测试（输入包含 @ 的内容）:")
    print()
    
    try:
        while True:
            result = smart_input.get_input("👤 你: ")
            
            if result.lower() in ['exit', 'quit']:
                break
            
            print(f"\n✅ 收到: {result}\n")
            
    except (KeyboardInterrupt, EOFError):
        print("\n\n👋 测试结束\n")


if __name__ == "__main__":
    main()

