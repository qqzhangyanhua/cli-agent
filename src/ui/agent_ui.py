"""
增强的用户界面和交互模块
集成性能监控和系统健康检查
"""

from src.core.agent_config import LLM_CONFIG, LLM_CONFIG2
from src.core.agent_memory import memory
from src.mcp.mcp_manager import mcp_manager
from src.ui.file_reference_parser import get_file_suggestions
from src.core.agent_llm import get_llm_stats, reset_llm_stats
from src.core.agent_metrics import get_metrics_collector
from src.core.agent_monitoring import get_monitoring_dashboard
from src.core.agent_resilience import get_resilience_manager


def print_header():
    """打印欢迎信息"""
    print("\n" + "=" * 80)
    print("🤖 AI智能终端助手 - 交互式版本 + MCP集成")
    print("=" * 80)
    print("\n✨ 功能:")
    print("  • 自然语言执行终端命令")
    print("  • 创建和执行代码文件")
    print("  • 智能问答")
    print("  • 对话记忆（记住上下文）")
    print("  • @ 文件引用（交互式文件选择）")
    print("\n🔌 MCP功能:")
    print("  • 文件系统: 读取/写入/列出/搜索文件")
    print("  • 桌面控制: 截图/剪贴板/执行命令")
    
    # 显示可用工具数量
    tools = mcp_manager.list_available_tools()
    fs_tools = [t for t in tools if t['type'] == 'filesystem']
    desktop_tools = [t for t in tools if t['type'] == 'desktop-commander']
    print(f"  • 已加载: {len(fs_tools)}个文件工具, {len(desktop_tools)}个桌面工具")
    
    print("\n🔧 双LLM配置:")
    print(f"  • 通用模型: {LLM_CONFIG['model']} (意图分析、问答)")
    print(f"  • 代码模型: {LLM_CONFIG2['model']} (命令生成、代码编写)")
    print("\n💡 特殊命令 (以 / 开头):")
    print("  • /exit 或 /quit  - 退出程序")
    print("  • /clear          - 清空对话历史")
    print("  • /history        - 查看对话历史")
    print("  • /commands       - 查看命令执行历史")
    print("  • /models         - 查看当前模型配置")
    print("  • /tools          - 查看MCP工具列表")
    print("  • /files          - 查看 @ 文件引用功能说明")
    print("  • /todos          - 查看今日待办事项")
    print("  • /stats          - 查看性能统计")
    print("  • /health         - 系统健康检查")
    print("  • /errors         - 查看错误统计")
    print("  • /reset          - 重置性能计数器")
    print("  • /help           - 显示详细帮助")
    print("\n" + "=" * 80 + "\n")


def handle_special_commands(user_input: str) -> bool:
    """
    处理特殊命令
    
    Returns:
        True: 退出程序
        False: 已处理，继续循环
        None: 未处理，继续正常流程
    """
    user_input_lower = user_input.lower().strip()
    
    # 退出命令
    if user_input_lower in ['/exit', '/quit', '/退出']:
        print("\n👋 再见！感谢使用AI智能终端助手！\n")
        return True
    
    # 清空历史
    if user_input_lower in ['/clear', '/清空']:
        memory.clear()
        print("\n✅ 对话历史已清空\n")
        return False
    
    # 查看对话历史
    if user_input_lower in ['/history', '/历史']:
        if not memory.history:
            print("\n暂无对话历史\n")
        else:
            print("\n📜 对话历史:")
            print("─" * 80)
            for idx, interaction in enumerate(memory.history, 1):
                print(f"\n[{interaction['timestamp']}]")
                print(f"👤 用户: {interaction['user']}")
                print(f"🤖 助手: {interaction['agent'][:200]}...")
                print(f"   (意图: {interaction['intent']})")
            print("─" * 80 + "\n")
        return False
    
    # 查看命令历史
    if user_input_lower in ['/commands', '/命令']:
        if not memory.command_history:
            print("\n暂无命令执行历史\n")
        else:
            print("\n📋 命令执行历史:")
            print("─" * 80)
            for cmd in memory.command_history:
                status = "✅" if cmd["success"] else "❌"
                print(f"{status} [{cmd['timestamp']}] {cmd['command']}")
            print("─" * 80 + "\n")
        return False
    
    # 查看模型配置
    if user_input_lower in ['/models', '/模型']:
        print("\n🔧 当前模型配置:")
        print("─" * 80)
        print("\n📌 通用模型 (LLM_CONFIG):")
        print(f"   模型: {LLM_CONFIG['model']}")
        print(f"   API: {LLM_CONFIG['base_url']}")
        print(f"   用途: 意图分析、智能问答、上下文理解")
        print(f"   使用场景: intent_analyzer(), question_answerer()")
        
        print("\n📌 代码生成模型 (LLM_CONFIG2):")
        print(f"   模型: {LLM_CONFIG2['model']}")
        print(f"   API: {LLM_CONFIG2['base_url']}")
        print(f"   用途: 命令生成、代码编写、任务规划")
        print(f"   使用场景: command_generator(), multi_step_planner(), mcp_tool_planner()")
        
        print("\n💡 提示:")
        print("   - 不同任务使用最适合的模型")
        print("   - 代码生成任务使用专业的代码模型")
        print("   - 对话和理解任务使用通用模型")
        print("─" * 80 + "\n")
        return False
    
    # 查看MCP工具列表
    if user_input_lower in ['/tools', '/工具']:
        print("\n🛠️ 可用的MCP工具:")
        print("─" * 80)
        tools = mcp_manager.list_available_tools()
        
        for tool_type in ['filesystem', 'desktop-commander']:
            type_tools = [t for t in tools if t['type'] == tool_type]
            if type_tools:
                icon = "📁" if tool_type == "filesystem" else "🖥️"
                print(f"\n{icon} {tool_type} ({len(type_tools)}个):")
                for t in type_tools:
                    params_str = ", ".join(t['params'][:3])
                    if len(t['params']) > 3:
                        params_str += "..."
                    print(f"   • {t['name']:25} - {t['description']}")
                    print(f"     参数: {params_str}")
        
        print("\n💡 使用示例:")
        print("   • '读取README.md文件'")
        print("   • '列出当前目录的所有Python文件'")
        print("   • '搜索包含LLM_CONFIG的文件'")
        print("   • '写入内容到test.txt文件'")
        print("─" * 80 + "\n")
        return False
    
    # 查看文件引用功能说明
    if user_input_lower in ['/files', '/文件', '/@']:
        print("\n📁 @ 文件引用功能说明:")
        print("─" * 80)
        print("\n🎯 基本用法:")
        print("  • 输入 @ 启动文件选择器")
        print("  • @readme 快速搜索匹配文件")
        print("  • 读取 @README.md")
        print("  • @config.py 的配置项有哪些？")
        print("  • 编辑 @src/main.py 添加日志功能")
        print("  • 比较 @old.txt 和 @new.txt 的差异")
        
        print("\n📝 支持的语法:")
        print("  • @filename.ext        - 智能匹配文件名")
        print("  • @./path/file.ext     - 相对路径")
        print("  • @/absolute/path      - 绝对路径")
        print("  • @*.py                - 通配符匹配")
        print("  • @folder/             - 目录引用")
        
        print("\n🔍 交互式选择:")
        print("  • 输入 @ 显示文件列表")
        print("  • 数字快速选择文件")
        print("  • 实时搜索和过滤")
        print("  • 支持分页浏览")
        print("  • 显示文件图标和大小")
        
        # 显示当前目录的一些文件作为示例
        suggestions = get_file_suggestions()
        if suggestions:
            print(f"\n💡 当前目录可用文件 (前10个):")
            for i, file in enumerate(suggestions[:10], 1):
                print(f"   {i:2d}. @{file}")
        
        print("\n✨ 功能特性:")
        print("  • 自动读取文件内容到上下文")
        print("  • 支持多文件同时引用")
        print("  • 与所有AI功能无缝集成")
        print("  • 智能错误处理和建议")
        
        print("\n🚀 使用示例:")
        print("  👤 用户: @")
        print("  🤖 助手: [显示交互式文件选择器]")
        print()
        print("  👤 用户: @read")
        print("  🤖 助手: [显示匹配'read'的文件列表]")
        print()
        print("  👤 用户: 读取 @README.md")
        print("  🤖 助手: [自动读取README.md内容并分析]")
        print("─" * 80 + "\n")
        return False
    
    # 查看帮助（添加新的/help命令）
    if user_input_lower in ['/help', '/帮助']:
        print("\n💡 特殊命令帮助:")
        print("─" * 80)
        print("\n🔧 可用命令:")
        print("  /exit, /quit      - 退出程序")
        print("  /clear            - 清空对话历史")
        print("  /history          - 查看对话历史")
        print("  /commands         - 查看命令执行历史")
        print("  /models           - 查看当前模型配置")
        print("  /tools            - 查看MCP工具列表")
        print("  /files            - 查看 @ 文件引用功能说明")
        print("  /todos            - 查看今日待办事项")
        print("  /help             - 显示此帮助信息")
        print("\n💡 文件引用:")
        print("  @ 或 @filename    - 引用文件并提问")
        print("\n🎯 使用提示:")
        print("  • 所有特殊命令以 / 开头")
        print("  • 可以使用中文或英文命令")
        print("  • 输入 @ 启动交互式文件选择器")
        print("─" * 80 + "\n")
        return False
    
    # 查看待办事项
    if user_input_lower in ['/todos', '/待办']:
        # 这里简单显示提示，实际待办查询会由工作流处理
        print("\n📋 提示: 请使用自然语言查询待办事项")
        print("例如: '今天有什么待办' 或 '查看所有待办'\n")
        return False
    
    # 查看性能统计
    if user_input_lower in ['/stats', '/统计']:
        metrics = get_metrics_collector()
        dashboard = get_monitoring_dashboard()
        
        print("\n📊 性能统计报告")
        print("─" * 80)
        print(dashboard.get_quick_stats())
        
        # LLM 统计
        llm_stats = get_llm_stats()
        print("🤖 LLM 使用统计:")
        for llm_name, stats in llm_stats.items():
            if llm_name != "session_summary":
                print(f"  • {stats['name']}: {stats['call_count']} 次调用, 成功率 {stats['success_rate']:.1%}")
        
        print(f"  • 总 Token: {llm_stats['session_summary']['total_tokens']['total']:,}")
        print("─" * 80 + "\n")
        return False
    
    # 系统健康检查
    if user_input_lower in ['/health', '/健康']:
        dashboard = get_monitoring_dashboard()
        health = dashboard.get_system_health()
        
        status_emoji = {"healthy": "🟢", "degraded": "🟡", "critical": "🔴"}
        print(f"\n{status_emoji.get(health.overall_status, '⚪')} 系统健康检查")
        print("─" * 80)
        print(f"整体状态: {health.overall_status.upper()}")
        print(f"性能分数: {health.performance_score:.1f}/100")
        print(f"检查时间: {health.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n📋 组件状态:")
        for comp_name, comp_data in health.components.items():
            status = comp_data["status"]
            emoji = status_emoji.get(status, "⚪")
            print(f"  {emoji} {comp_name}: {status}")
            
            if comp_data.get("issues"):
                for issue in comp_data["issues"]:
                    print(f"    ⚠️ {issue}")
        
        if health.recommendations:
            print("\n💡 优化建议:")
            for rec in health.recommendations:
                print(f"  • {rec}")
        
        print("─" * 80 + "\n")
        return False
    
    # 查看错误统计
    if user_input_lower in ['/errors', '/错误']:
        resilience = get_resilience_manager()
        status = resilience.get_health_status()
        
        print("\n🚨 错误统计报告")
        print("─" * 80)
        print(f"总错误数: {status['total_errors']}")
        print(f"恢复次数: {status['total_recoveries']}")
        print(f"恢复率: {status['recovery_rate']:.1%}")
        
        if status['error_stats']:
            print("\n📊 错误分类:")
            for error_type, count in status['error_stats'].items():
                print(f"  • {error_type}: {count} 次")
        
        if status['circuit_breakers']:
            print("\n🔴 熔断器状态:")
            for name, breaker in status['circuit_breakers'].items():
                state_emoji = {"OPEN": "🔴", "CLOSED": "🟢", "HALF_OPEN": "🟡"}
                emoji = state_emoji.get(breaker['state'], "⚪")
                print(f"  {emoji} {name}: {breaker['state']} (失败: {breaker['failure_count']})")
        
        print("─" * 80 + "\n")
        return False
    
    # 重置性能计数器
    if user_input_lower in ['/reset', '/重置']:
        metrics = get_metrics_collector()
        resilience = get_resilience_manager()
        
        # 重置各种统计
        metrics.reset_session_stats()
        resilience.reset_stats()
        reset_llm_stats()
        
        print("\n✅ 性能计数器已重置")
        print("  • 会话统计已清空")
        print("  • 错误统计已清空") 
        print("  • LLM 统计已清空")
        print("  • 熔断器状态已重置\n")
        return False
    
    return None
