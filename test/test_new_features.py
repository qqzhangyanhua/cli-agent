"""
测试新增的数据转换和环境诊断功能
"""

import sys
import json
from pathlib import Path

# 添加项目路径
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

from data_converter_tools import data_converter_tools, DataConverter
from env_diagnostic_tools import env_diagnostic_tools


def test_data_conversion():
    """测试数据转换功能"""
    print("\n" + "="*80)
    print("测试数据转换功能")
    print("="*80)
    
    # 测试 JSON to CSV
    print("\n1. 测试 JSON 转 CSV:")
    json_data = '''[
        {"name": "Alice", "age": 30, "city": "Beijing"},
        {"name": "Bob", "age": 25, "city": "Shanghai"},
        {"name": "Charlie", "age": 35, "city": "Guangzhou"}
    ]'''
    
    result = data_converter_tools.convert(
        content=json_data,
        source_format="json",
        target_format="csv"
    )
    
    if result["success"]:
        print("✅ 转换成功:")
        print(result["result"])
    else:
        print(f"❌ 转换失败: {result['error']}")
    
    # 测试 JSON 验证
    print("\n2. 测试 JSON 验证:")
    valid_json = '{"name": "test", "value": 123}'
    result = data_converter_tools.validate(valid_json, "json")
    print(f"有效JSON: {result['message']}")
    
    invalid_json = '{"name": "test", "value": 123'  # 缺少结束括号
    result = data_converter_tools.validate(invalid_json, "json")
    print(f"无效JSON: {result['message']}")
    
    # 测试 JSON 美化
    print("\n3. 测试 JSON 美化:")
    ugly_json = '{"name":"test","age":30,"items":[1,2,3]}'
    result = data_converter_tools.beautify(ugly_json, "json")
    if result["success"]:
        print("✅ 美化成功:")
        print(result["result"])
    
    # 测试 YAML 转 JSON
    print("\n4. 测试 YAML 转 JSON:")
    yaml_data = '''
name: Test Project
version: 1.0.0
dependencies:
  - requests
  - flask
'''
    result = data_converter_tools.convert(
        content=yaml_data,
        source_format="yaml",
        target_format="json"
    )
    if result["success"]:
        print("✅ 转换成功:")
        print(result["result"])


def test_env_diagnostic():
    """测试环境诊断功能"""
    print("\n" + "="*80)
    print("测试环境诊断功能")
    print("="*80)
    
    # 执行诊断
    print("\n执行环境诊断...")
    result = env_diagnostic_tools.full_diagnostic()
    
    if result["success"]:
        report = result["report"]
        
        # 格式化并打印报告
        formatted_report = env_diagnostic_tools.format_report(report)
        print(formatted_report)
        
        # 显示详细的问题和建议
        summary = report.get("summary", {})
        print("\n详细信息:")
        print(f"  - 总问题数: {summary.get('total_issues', 0)}")
        print(f"  - Python版本: {report.get('python_env', {}).get('python_version', 'unknown')}")
        print(f"  - 虚拟环境状态: {report.get('python_env', {}).get('virtual_env', 'unknown')}")
    else:
        print(f"❌ 诊断失败: {result.get('error', 'unknown')}")


def test_format_detection():
    """测试格式自动检测"""
    print("\n" + "="*80)
    print("测试格式自动检测")
    print("="*80)
    
    converter = DataConverter()
    
    test_cases = [
        ('{"name": "test"}', "json"),
        ('[1, 2, 3]', "json"),
        ('name: test\nvalue: 123', "yaml"),
        ('name,age,city\nAlice,30,Beijing', "csv"),
        ('<root><item>test</item></root>', "xml"),
    ]
    
    for content, expected in test_cases:
        detected = converter.detect_format(content)
        status = "✅" if detected == expected else "❌"
        print(f"{status} 输入: {content[:30]:30s} -> 检测: {detected:8s} (期望: {expected})")


if __name__ == "__main__":
    print("\n🧪 开始测试新功能...\n")
    
    try:
        # 测试数据转换
        test_data_conversion()
        
        # 测试格式检测
        test_format_detection()
        
        # 测试环境诊断
        test_env_diagnostic()
        
        print("\n" + "="*80)
        print("✅ 所有测试完成")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
