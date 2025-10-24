#!/usr/bin/env python3
"""
日报助手功能演示脚本

展示如何使用 DNM 智能体的自动日报功能
"""

import os
import sys
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.daily_report_tools import (
    DailyReportCollector,
    DailyReportGenerator,
    generate_daily_report_func
)
from src.core.agent_memory import memory


def demo_data_collection():
    """演示数据收集功能"""
    print("🎯 演示1: 数据收集功能")
    print("=" * 60)
    
    collector = DailyReportCollector()
    data = collector.collect_all_data()
    
    print(f"📅 收集日期: {data['date']}")
    print(f"📊 项目信息: {data['project']['name']}")
    print(f"🌿 Git 分支: {data['project']['git_branch']}")
    print(f"📝 Git 提交: {len(data['git_commits'])} 条")
    print(f"💻 命令记录: {len(data['commands'])} 条")
    print(f"💬 对话记录: {len(data['conversations'])} 条")
    
    if data['git_commits']:
        print("\n最近的 Git 提交:")
        for commit in data['git_commits'][:3]:
            print(f"  • {commit['hash']} - {commit['message']}")
    
    if data['commands']:
        print("\n最近的命令:")
        for cmd in data['commands'][:3]:
            status = "✅" if cmd['success'] else "❌"
            print(f"  {status} {cmd['command']}")
    
    print()
    return data


def demo_report_generation(data):
    """演示日报生成功能"""
    print("🎯 演示2: 日报生成功能")
    print("=" * 60)
    
    generator = DailyReportGenerator()
    
    # 演示不同模板
    templates = ["summary", "standard", "technical"]
    
    for template in templates:
        print(f"\n📝 生成 {template} 模板日报...")
        try:
            # 由于可能没有网络连接，这里会使用降级策略
            report = generator.generate_report(data, template)
            print(f"✅ {template} 模板生成成功")
            print(f"📄 报告长度: {len(report)} 字符")
            
            # 显示报告预览
            preview = report[:150] + "..." if len(report) > 150 else report
            print(f"📖 预览:\n{preview}")
            
        except Exception as e:
            print(f"❌ {template} 模板生成失败: {e}")


def demo_tool_function():
    """演示工具函数调用"""
    print("🎯 演示3: 工具函数调用")
    print("=" * 60)
    
    import json
    
    # 演示基本调用
    print("📝 基本调用...")
    try:
        result = generate_daily_report_func("")
        print("✅ 基本调用成功")
        lines = result.split('\n')
        print(f"📄 结果行数: {len(lines)}")
        print(f"📖 前3行预览:")
        for line in lines[:3]:
            if line.strip():
                print(f"  {line}")
    except Exception as e:
        print(f"❌ 基本调用失败: {e}")
    
    # 演示参数调用
    print("\n📝 带参数调用...")
    try:
        params = {
            "template": "summary",
            "save_file": False
        }
        result = generate_daily_report_func(json.dumps(params, ensure_ascii=False))
        print("✅ 带参数调用成功")
        lines = result.split('\n')
        print(f"📄 结果行数: {len(lines)}")
    except Exception as e:
        print(f"❌ 带参数调用失败: {e}")


def demo_memory_integration():
    """演示记忆系统集成"""
    print("🎯 演示4: 记忆系统集成")
    print("=" * 60)
    
    # 添加一些演示数据
    memory.add_interaction(
        "生成日报",
        "正在生成今日工作日报...",
        "daily_report"
    )
    
    memory.add_interaction(
        "今天做了什么",
        "今天主要完成了日报助手功能的开发和测试",
        "question"
    )
    
    memory.add_command(
        "git log --oneline -5",
        "abc1234 feat: 添加日报助手功能",
        True
    )
    
    memory.add_command(
        "python test_daily_report.py",
        "测试通过",
        True
    )
    
    print("✅ 已添加演示数据到记忆系统")
    print(f"📊 对话历史: {len(memory.history)} 条")
    print(f"💻 命令历史: {len(memory.command_history)} 条")
    
    # 重新收集数据，应该包含新添加的记忆
    collector = DailyReportCollector()
    data = collector.collect_all_data()
    
    print(f"✅ 从记忆收集到:")
    print(f"   💬 对话: {len(data['conversations'])} 条")
    print(f"   💻 命令: {len(data['commands'])} 条")
    
    # 显示收集到的对话
    if data['conversations']:
        print("\n收集到的对话:")
        for conv in data['conversations']:
            print(f"  • [{conv.get('time', '')}] {conv['user_input'][:30]}...")


def demo_usage_examples():
    """演示使用示例"""
    print("🎯 演示5: 实际使用示例")
    print("=" * 60)
    
    print("📋 在 DNM 智能体中使用日报功能:")
    print()
    print("1️⃣ 交互模式:")
    print("   $ dnm")
    print("   👤 你: 生成日报")
    print("   🤖 助手: [自动收集数据并生成日报]")
    print()
    print("2️⃣ 单次命令模式:")
    print("   $ dnm \"生成日报\"")
    print("   $ dnm \"今日总结\"")
    print("   $ dnm \"工作报告\"")
    print()
    print("3️⃣ 特殊命令:")
    print("   👤 你: /report")
    print("   🤖 助手: 提示使用自然语言生成日报")
    print()
    print("4️⃣ 日报文件保存:")
    print("   📁 默认保存到: daily_reports/daily_report_YYYY-MM-DD.md")
    print("   📝 支持三种模板: standard, technical, summary")
    print()
    print("5️⃣ 配置选项:")
    print("   • DEFAULT_DAILY_REPORT_TEMPLATE: 默认模板")
    print("   • DAILY_REPORT_DIR: 保存目录")
    print("   • AUTO_SAVE_DAILY_REPORT: 自动保存开关")


def main():
    """主演示函数"""
    print("🚀 DNM 智能体 - 日报助手功能演示")
    print("=" * 80)
    print(f"📅 演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    try:
        # 1. 数据收集演示
        data = demo_data_collection()
        
        # 2. 日报生成演示
        demo_report_generation(data)
        
        # 3. 工具函数演示
        demo_tool_function()
        
        # 4. 记忆集成演示
        demo_memory_integration()
        
        # 5. 使用示例
        demo_usage_examples()
        
        print("\n🎉 演示完成！")
        print("=" * 80)
        print("💡 提示:")
        print("   • 日报功能已集成到 DNM 智能体中")
        print("   • 使用 'dnm \"生成日报\"' 即可体验完整功能")
        print("   • 支持多种日报模板和自定义配置")
        print("   • 所有数据自动收集，无需手动输入")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
