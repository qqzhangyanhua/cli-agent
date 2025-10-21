#!/usr/bin/env python3
"""
交互式文件选择器测试脚本
"""

import os
import sys
from pathlib import Path

# 添加项目目录到Python路径
SCRIPT_DIR = Path(__file__).parent.absolute()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from interactive_file_selector import InteractiveFileSelector, interactive_file_select, quick_file_select


def test_file_selector_display():
    """测试文件选择器显示功能"""
    print("🧪 测试交互式文件选择器显示功能")
    print("=" * 60)
    
    selector = InteractiveFileSelector()
    
    # 获取文件列表
    files = selector.get_files_list()
    print(f"📁 当前目录文件数量: {len(files)}")
    
    # 测试文件过滤
    test_filters = ["agent", "test", "README", "*.py"]
    
    for filter_text in test_filters:
        filtered = selector.filter_files(files, filter_text)
        print(f"🔍 过滤 '{filter_text}': 找到 {len(filtered)} 个匹配")
        
        for i, file in enumerate(filtered[:3], 1):  # 只显示前3个
            print(f"  {i}. {file['icon']} {file['name']}")
    
    print("\n✅ 显示功能测试完成！")


def test_quick_select():
    """测试快速选择功能"""
    print("\n🧪 测试快速选择功能")
    print("=" * 60)
    
    # 模拟快速选择测试
    test_searches = ["agent", "README", "config", "nonexistent"]
    
    for search_term in test_searches:
        print(f"\n🔍 快速搜索: '{search_term}'")
        
        selector = InteractiveFileSelector()
        files = selector.get_files_list()
        filtered = selector.filter_files(files, search_term)
        
        if filtered:
            print(f"  找到 {len(filtered)} 个匹配:")
            for i, file in enumerate(filtered[:5], 1):
                print(f"    {i}. {file['icon']} {file['name']}")
        else:
            print("  ❌ 未找到匹配文件")
    
    print("\n✅ 快速选择测试完成！")


def test_file_icons():
    """测试文件图标功能"""
    print("\n🧪 测试文件图标功能")
    print("=" * 60)
    
    selector = InteractiveFileSelector()
    
    # 测试不同类型文件的图标
    test_files = [
        "test.py", "script.js", "style.css", "data.json",
        "README.md", "document.txt", "image.png", "video.mp4",
        "archive.zip", "program.exe", "script.sh"
    ]
    
    for filename in test_files:
        path = Path(filename)
        icon = selector._get_file_icon(path)
        print(f"  {icon} {filename}")
    
    print("\n✅ 文件图标测试完成！")


def demo_interactive_usage():
    """演示交互式使用方法"""
    print("\n🎯 交互式文件选择器使用演示")
    print("=" * 60)
    
    print("\n📖 使用方法:")
    print("1. 在 AI 智能体中输入 '@' 启动文件选择器")
    print("2. 输入数字选择文件")
    print("3. 输入文件名进行搜索")
    print("4. 使用 'n'/'p' 翻页，'q' 退出")
    
    print("\n🎮 交互命令:")
    print("  • 数字 (1-15)  - 选择对应文件")
    print("  • 文件名       - 搜索过滤")
    print("  • n           - 下一页")
    print("  • p           - 上一页") 
    print("  • r           - 刷新列表")
    print("  • h           - 显示/隐藏隐藏文件")
    print("  • q/exit      - 退出选择器")
    
    print("\n💡 智能特性:")
    print("  • 自动高亮匹配文本")
    print("  • 显示文件大小和图标")
    print("  • 支持模糊搜索")
    print("  • 单个匹配时自动确认")
    
    print("\n🚀 实际使用示例:")
    print("  👤 输入: @")
    print("  🤖 显示: [文件选择器界面]")
    print("  👤 输入: 5")
    print("  🤖 选择: agent_config.py")
    print()
    print("  👤 输入: @read")
    print("  🤖 显示: [匹配'read'的文件列表]")
    print("  👤 输入: 1")
    print("  🤖 选择: README.md")


def create_demo_files():
    """创建演示文件"""
    demo_files = [
        ("demo_config.json", '{"name": "demo", "version": "1.0"}'),
        ("demo_script.py", "# Demo Python script\nprint('Hello World')"),
        ("demo_readme.md", "# Demo Project\nThis is a demo file."),
        ("demo_data.txt", "Sample data file\nLine 1\nLine 2"),
    ]
    
    print("\n📝 创建演示文件...")
    for filename, content in demo_files:
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ 创建: {filename}")
        except Exception as e:
            print(f"  ❌ 创建失败 {filename}: {e}")


def cleanup_demo_files():
    """清理演示文件"""
    demo_files = ["demo_config.json", "demo_script.py", "demo_readme.md", "demo_data.txt"]
    
    print("\n🧹 清理演示文件...")
    for filename in demo_files:
        try:
            if os.path.exists(filename):
                os.remove(filename)
                print(f"  ✅ 删除: {filename}")
        except Exception as e:
            print(f"  ❌ 删除失败 {filename}: {e}")


if __name__ == "__main__":
    try:
        print("🎯 交互式文件选择器测试套件")
        print("=" * 80)
        
        # 创建演示文件
        create_demo_files()
        
        # 运行测试
        test_file_selector_display()
        test_quick_select()
        test_file_icons()
        demo_interactive_usage()
        
        print("\n" + "=" * 80)
        print("🎉 所有测试完成！交互式文件选择器已准备就绪。")
        
        print("\n📚 现在您可以:")
        print("  1. 运行 ./ai-agent 启动智能体")
        print("  2. 输入 @ 体验交互式文件选择")
        print("  3. 输入 @部分文件名 进行快速搜索")
        print("  4. 输入 files 查看完整功能说明")
        
        # 清理演示文件
        cleanup_demo_files()
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        cleanup_demo_files()
        sys.exit(1)
