"""
用户界面和交互模块
"""

from agent_config import LLM_CONFIG, LLM_CONFIG2
from agent_memory import memory
from mcp_manager import mcp_manager


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
    print("\n💡 特殊命令:")
    print("  • 'exit' 或 'quit' - 退出程序")
    print("  • 'clear' - 清空对话历史")
    print("  • 'history' - 查看对话历史")
    print("  • 'commands' - 查看命令执行历史")
    print("  • 'models' - 查看当前模型配置")
    print("  • 'tools' - 查看MCP工具列表")
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
    if user_input_lower in ['exit', 'quit', '退出']:
        print("\n👋 再见！感谢使用AI智能终端助手！\n")
        return True
    
    # 清空历史
    if user_input_lower in ['clear', '清空']:
        memory.clear()
        print("\n✅ 对话历史已清空\n")
        return False
    
    # 查看对话历史
    if user_input_lower in ['history', '历史']:
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
    if user_input_lower in ['commands', '命令']:
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
    if user_input_lower in ['models', '模型']:
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
    if user_input_lower in ['tools', '工具']:
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
    
    return None
