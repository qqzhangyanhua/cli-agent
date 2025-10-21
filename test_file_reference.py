#!/usr/bin/env python3
"""
@ 文件引用功能测试脚本
"""

import os
import sys
from pathlib import Path

# 添加项目目录到Python路径
SCRIPT_DIR = Path(__file__).parent.absolute()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from file_reference_parser import FileReferenceParser, parse_file_references


def test_file_reference_parsing():
    """测试文件引用解析功能"""
    print("🧪 测试 @ 文件引用解析功能")
    print("=" * 60)
    
    # 创建测试文件
    test_files = [
        "test_readme.md",
        "test_config.py", 
        "test_data.json"
    ]
    
    for file in test_files:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(f"# 这是测试文件 {file}\n内容示例...")
    
    # 测试用例
    test_cases = [
        "读取 @test_readme.md 的内容",
        "@test_config.py 中有什么配置？",
        "比较 @test_data.json 和 @test_config.py",
        "查看 @*.py 文件",
        "显示 @nonexistent.txt 内容",
        "分析 @test 文件"
    ]
    
    parser = FileReferenceParser()
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n📝 测试 {i}: {test_input}")
        print("-" * 40)
        
        processed_text, references = parser.parse_references(test_input)
        
        print(f"原始输入: {test_input}")
        print(f"处理后: {processed_text}")
        print(f"找到引用: {len(references)} 个")
        
        for ref in references:
            status = "✅" if ref.exists else "❌"
            print(f"  {status} {ref.file_path} (置信度: {ref.match_confidence:.1%})")
    
    # 清理测试文件
    for file in test_files:
        try:
            os.remove(file)
        except:
            pass
    
    print("\n✅ 测试完成！")


def test_smart_matching():
    """测试智能匹配功能"""
    print("\n🔍 测试智能文件匹配")
    print("=" * 60)
    
    parser = FileReferenceParser()
    
    # 测试部分文件名匹配
    test_patterns = [
        "readme",  # 应该匹配 README.md
        "config",  # 应该匹配 agent_config.py
        "agent",   # 应该匹配多个 agent_*.py 文件
        "*.py",    # 通配符匹配
    ]
    
    for pattern in test_patterns:
        print(f"\n🔎 搜索模式: '{pattern}'")
        references = parser._smart_file_search(f"@{pattern}", pattern)
        
        if references:
            print(f"找到 {len(references)} 个匹配:")
            for ref in references[:5]:  # 只显示前5个
                print(f"  • {ref.file_path} (置信度: {ref.match_confidence:.1%})")
        else:
            print("  未找到匹配文件")


def test_file_suggestions():
    """测试文件建议功能"""
    print("\n💡 测试文件建议功能")
    print("=" * 60)
    
    parser = FileReferenceParser()
    
    # 获取所有文件建议
    all_suggestions = parser.get_file_suggestions()
    print(f"当前目录文件建议 ({len(all_suggestions)} 个):")
    for i, file in enumerate(all_suggestions[:10], 1):
        print(f"  {i:2d}. {file}")
    
    # 测试部分匹配
    partial_tests = ["agent", "test", "README"]
    
    for partial in partial_tests:
        suggestions = parser.get_file_suggestions(partial)
        print(f"\n以 '{partial}' 开头的文件:")
        for file in suggestions[:5]:
            print(f"  • {file}")


if __name__ == "__main__":
    try:
        test_file_reference_parsing()
        test_smart_matching()
        test_file_suggestions()
        
        print("\n🎉 所有测试完成！@ 文件引用功能已准备就绪。")
        print("\n📖 使用方法:")
        print("  ./ai-agent")
        print("  👤 你: 读取 @README.md")
        print("  👤 你: @agent_config.py 中的配置有哪些？")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        sys.exit(1)
