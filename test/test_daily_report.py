#!/usr/bin/env python3
"""
日报助手功能测试
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.daily_report_tools import (
    DailyReportCollector,
    DailyReportGenerator,
    generate_daily_report_func
)
from src.core.agent_memory import memory


def test_data_collection():
    """测试数据收集功能"""
    print("🧪 测试数据收集功能...")
    
    collector = DailyReportCollector()
    data = collector.collect_all_data()
    
    print(f"✅ 收集到的数据:")
    print(f"   📅 日期: {data['date']}")
    print(f"   📝 Git 提交: {len(data['git_commits'])} 条")
    print(f"   💻 命令记录: {len(data['commands'])} 条")
    print(f"   💬 对话记录: {len(data['conversations'])} 条")
    print(f"   📊 项目信息: {data['project']['name']}")
    
    return data


def test_report_generation():
    """测试日报生成功能"""
    print("\n🧪 测试日报生成功能...")
    
    # 模拟一些数据
    test_data = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "project": {
            "name": "DNM智能体",
            "path": "/Users/zhangyanhua/Desktop/AI/tushare/quantification/example",
            "git_branch": "main",
            "git_status": "工作区干净"
        },
        "git_commits": [
            {
                "hash": "abc12345",
                "author": "Developer",
                "time": "10:30:00",
                "message": "feat: 添加日报助手功能",
                "full_hash": "abc1234567890"
            }
        ],
        "commands": [
            {
                "command": "git status",
                "output": "On branch main",
                "success": True,
                "time": "10:25:00"
            },
            {
                "command": "python test_daily_report.py",
                "output": "测试运行中...",
                "success": True,
                "time": "10:35:00"
            }
        ],
        "conversations": [
            {
                "user_input": "生成日报",
                "agent_response": "正在生成日报...",
                "intent": "daily_report",
                "time": "10:40:00"
            }
        ],
        "collection_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    generator = DailyReportGenerator()
    
    # 测试不同模板
    templates = ["standard", "technical", "summary"]
    
    for template in templates:
        print(f"\n📝 测试 {template} 模板...")
        try:
            report = generator.generate_report(test_data, template)
            print(f"✅ {template} 模板生成成功")
            print(f"📄 报告长度: {len(report)} 字符")
            
            # 显示报告的前200个字符
            preview = report[:200] + "..." if len(report) > 200 else report
            print(f"📖 预览:\n{preview}")
            
        except Exception as e:
            print(f"❌ {template} 模板生成失败: {e}")
    
    return test_data


def test_tool_function():
    """测试工具函数"""
    print("\n🧪 测试工具函数...")
    
    # 测试基本调用
    print("📝 测试基本调用...")
    try:
        result = generate_daily_report_func("")
        print("✅ 基本调用成功")
        print(f"📄 结果长度: {len(result)} 字符")
    except Exception as e:
        print(f"❌ 基本调用失败: {e}")
    
    # 测试带参数调用
    print("\n📝 测试带参数调用...")
    try:
        params = {
            "template": "summary",
            "save_file": False
        }
        result = generate_daily_report_func(json.dumps(params, ensure_ascii=False))
        print("✅ 带参数调用成功")
        print(f"📄 结果长度: {len(result)} 字符")
    except Exception as e:
        print(f"❌ 带参数调用失败: {e}")


def test_memory_integration():
    """测试与记忆系统的集成"""
    print("\n🧪 测试记忆系统集成...")
    
    # 添加一些测试数据到记忆中
    memory.add_interaction(
        "生成日报",
        "正在生成日报...",
        "daily_report"
    )
    
    memory.add_command(
        "git log --oneline -5",
        "abc1234 feat: 添加日报功能\ndef5678 fix: 修复bug",
        True
    )
    
    print("✅ 已添加测试数据到记忆")
    print(f"📊 对话历史: {len(memory.history)} 条")
    print(f"💻 命令历史: {len(memory.command_history)} 条")
    
    # 测试数据收集
    collector = DailyReportCollector()
    data = collector.collect_all_data()
    
    print(f"✅ 从记忆收集到:")
    print(f"   💬 对话: {len(data['conversations'])} 条")
    print(f"   💻 命令: {len(data['commands'])} 条")


def main():
    """主测试函数"""
    print("🚀 开始日报助手功能测试\n")
    
    try:
        # 1. 测试数据收集
        data = test_data_collection()
        
        # 2. 测试日报生成
        test_data = test_report_generation()
        
        # 3. 测试工具函数
        test_tool_function()
        
        # 4. 测试记忆集成
        test_memory_integration()
        
        print("\n🎉 所有测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
