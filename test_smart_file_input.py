#!/usr/bin/env python3
"""
测试智能文件输入功能

这个脚本用于测试新的 @ 文件引用功能，包括：
- prompt_toolkit 自动补全
- 文件搜索和匹配
- 降级模式
"""

import sys
import os
from pathlib import Path

# 添加项目目录到路径
SCRIPT_DIR = Path(__file__).parent.absolute()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from smart_file_input import (
    SmartFileInput,
    FileCompleter,
    check_prompt_toolkit_available,
)


def test_prompt_toolkit_availability():
    """测试 prompt_toolkit 是否可用"""
    print("=" * 60)
    print("📦 测试 prompt_toolkit 可用性")
    print("=" * 60)
    
    if check_prompt_toolkit_available():
        print("✅ prompt-toolkit 已安装并可用")
        try:
            import prompt_toolkit
            print(f"   版本: {prompt_toolkit.__version__}")
        except Exception as e:
            print(f"   ⚠️  无法获取版本信息: {e}")
    else:
        print("❌ prompt-toolkit 未安装或不可用")
        print("   💡 运行以下命令安装:")
        print("   pip install prompt-toolkit>=3.0.0")
    
    print()


def test_file_completer():
    """测试文件补全器"""
    print("=" * 60)
    print("📂 测试文件补全器")
    print("=" * 60)
    
    try:
        completer = FileCompleter()
        
        # 刷新文件缓存
        print("🔄 扫描文件系统...")
        completer._refresh_file_cache()
        
        print(f"✅ 找到 {len(completer._file_cache)} 个文件")
        
        # 显示前 10 个文件
        print("\n📁 文件列表（前 10 个）:")
        for i, file_item in enumerate(completer._file_cache[:10], 1):
            type_str = "目录" if file_item.is_dir else completer._format_file_size(file_item.size)
            print(f"   {i}. {file_item.icon} {file_item.relative_path:<30} ({type_str})")
        
        if len(completer._file_cache) > 10:
            print(f"   ... 还有 {len(completer._file_cache) - 10} 个文件")
        
        print()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        print()


def test_fuzzy_match():
    """测试模糊匹配功能"""
    print("=" * 60)
    print("🔍 测试模糊匹配算法")
    print("=" * 60)
    
    try:
        completer = FileCompleter()
        
        # 测试用例
        test_cases = [
            ("readme", "README.md"),
            ("cfg", "agent_config.py"),
            ("wkf", "agent_workflow.py"),
            ("ui", "agent_ui.py"),
            ("test", "test_demo.py"),
        ]
        
        print("\n测试匹配结果:")
        for query, filename in test_cases:
            is_match, score = completer._fuzzy_match(query, filename)
            status = "✅" if is_match else "❌"
            print(f"   {status} '{query}' → '{filename}' (得分: {score})")
        
        print()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        print()


def test_smart_input_basic():
    """测试基础输入功能"""
    print("=" * 60)
    print("⌨️  测试智能输入（基础功能）")
    print("=" * 60)
    
    try:
        smart_input = SmartFileInput()
        
        print("✅ SmartFileInput 实例创建成功")
        print(f"   工作目录: {smart_input.working_dir}")
        
        if check_prompt_toolkit_available():
            print("   模式: 增强模式 (prompt_toolkit)")
            print("\n💡 要测试交互功能，请运行:")
            print("   python3 test_smart_file_input.py --interactive")
        else:
            print("   模式: 降级模式 (基础输入)")
        
        print()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        print()


def test_file_icons():
    """测试文件图标映射"""
    print("=" * 60)
    print("🎨 测试文件图标")
    print("=" * 60)
    
    try:
        completer = FileCompleter()
        
        # 测试不同文件类型
        test_files = [
            "test.py",
            "test.js",
            "test.ts",
            "test.md",
            "test.json",
            "test.html",
            "test.css",
            "test.txt",
            "test.pdf",
            "test.jpg",
            "test.mp4",
            "test.zip",
            "test.unknown",
        ]
        
        print("\n文件类型 → 图标映射:")
        for filename in test_files:
            path = Path(filename)
            icon = completer._get_file_icon(path)
            print(f"   {icon} {filename}")
        
        print()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        print()


def interactive_test():
    """交互式测试"""
    print("=" * 60)
    print("🎮 交互式测试模式")
    print("=" * 60)
    print()
    print("💡 在下面的输入框中测试 @ 文件引用功能")
    print("   - 输入 @ 后继续输入文件名")
    print("   - 使用上下箭头选择文件")
    print("   - 按 Enter 确认选择")
    print("   - 按 Ctrl+C 退出测试")
    print()
    
    if not check_prompt_toolkit_available():
        print("⚠️  prompt-toolkit 未安装，将使用降级模式")
        print()
    
    try:
        smart_input = SmartFileInput()
        
        while True:
            try:
                user_input = smart_input.get_input("👤 测试输入: ")
                print(f"✅ 收到输入: {user_input}")
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("\n👋 退出测试\n")
                    break
                
                # 检查是否包含文件引用
                if '@' in user_input:
                    import re
                    matches = re.findall(r'@([^\s]+)', user_input)
                    if matches:
                        print(f"📁 检测到文件引用: {', '.join(matches)}")
                
                print()
                
            except (KeyboardInterrupt, EOFError):
                print("\n\n👋 退出测试\n")
                break
                
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("\n🧪 智能文件输入功能测试\n")
    
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] in ['--interactive', '-i']:
        interactive_test()
        return
    
    # 运行所有测试
    test_prompt_toolkit_availability()
    test_file_completer()
    test_fuzzy_match()
    test_smart_input_basic()
    test_file_icons()
    
    # 总结
    print("=" * 60)
    print("✨ 测试完成")
    print("=" * 60)
    print()
    print("💡 提示:")
    print("   - 运行 'python3 test_smart_file_input.py --interactive'")
    print("     进行交互式测试")
    print("   - 运行 'dnm' 或 'ai-agent' 体验完整功能")
    print()
    
    if not check_prompt_toolkit_available():
        print("⚠️  建议安装 prompt-toolkit 以获得最佳体验:")
        print("   pip install prompt-toolkit>=3.0.0")
        print()


if __name__ == "__main__":
    main()

